import os
import time
from typing import Generator

import pytest
from app.autonomous.alert_engine import AlertEngine
from app.autonomous.autonomous_manager import AutonomousManager
from app.autonomous.notification_engine import NotificationEngine
from app.autonomous.reminder_engine import ReminderEngine
from app.autonomous.scheduler import Scheduler
from app.core.config import settings
from app.core.container import Container
from app.orchestrator.orchestrator import AgentOrchestrator
from app.personalization.models import (
    Reminder,
)
from app.schemas.requests import ExecutionRequest


@pytest.fixture
def temp_notif_db_path() -> Generator[str, None, None]:
    path = "./data/test_notification_history.json"
    if os.path.exists(path):
        os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_priority_scoring() -> None:
    """Verifies priority engine correctly resolves Critical, High, Medium, Low based on urgency/impact."""
    container = Container(settings)
    manager = AutonomousManager(container)

    # 1. Critical event (due in 5 hours, high impact warning)
    crit_pri = manager.calculate_priority_score(
        due_date=time.time() + 5000.0,
        urgency_factor=0.0,
        impact_factor=9.0
    )
    assert crit_pri == "critical"

    # 2. High event (due in 2 days, moderate-high impact)
    high_pri = manager.calculate_priority_score(
        due_date=time.time() + 1.5 * 86400.0,
        urgency_factor=0.0,
        impact_factor=7.5
    )
    assert high_pri == "high"

    # 3. Medium event (due in 5 days, moderate impact)
    med_pri = manager.calculate_priority_score(
        due_date=time.time() + 5 * 86400.0,
        urgency_factor=0.0,
        impact_factor=5.0
    )
    assert med_pri == "medium"

    # 4. Low event (due in 2 weeks, minor impact)
    low_pri = manager.calculate_priority_score(
        due_date=time.time() + 15 * 86400.0,
        urgency_factor=0.0,
        impact_factor=2.0
    )
    assert low_pri == "low"


def test_scheduler_jobs() -> None:
    """Verifies periodic job scheduling and event-driven trigger callbacks."""
    scheduler = Scheduler()
    flag = {"triggered": False, "event_triggered": False}

    def dummy_daily_callback() -> None:
        flag["triggered"] = True

    def dummy_event_callback() -> None:
        flag["event_triggered"] = True

    # Register jobs
    scheduler.register_job("test_daily", "daily", dummy_daily_callback)
    scheduler.register_job("scheme_deadline_passed", "event_driven", dummy_event_callback)

    # Execute daily jobs
    count = scheduler.run_periodic_jobs("daily")
    assert count == 1
    assert flag["triggered"] is True

    # Trigger custom event
    evt_count = scheduler.trigger_event("scheme_deadline_passed")
    assert evt_count == 1
    assert flag["event_triggered"] is True


def test_reminder_generation() -> None:
    """Verifies reminders generated for crop activities, scheme deadlines, and documents."""
    container = Container(settings)
    reminder_eng = ReminderEngine(container)

    twin_state = {
        "predictions": {
            "next_crop": "Rice",
            "water_demand_liters": 1500000.0,
            "scheme_eligibility_changes": {
                "eligible_new_schemes": ["PM-Kisan"]
            }
        },
        "twin": {
            "irrigation_type": "rainfed"
        }
    }

    rems = reminder_eng.generate_reminders("farmer_autonomous_test_1", twin_state)
    assert len(rems) > 0
    # Schemes eligibility reminder
    assert any("PM-Kisan" in r.message for r in rems)
    # Water demand / irrigation reminder
    assert any("irrigation" in r.message.lower() for r in rems)
    # Next season crop sowing activity preparation
    assert any("Prepare field" in r.message for r in rems)


def test_alert_generation() -> None:
    """Verifies hazard warnings generated for weather risks, disease probability, and budget overruns."""
    container = Container(settings)
    alert_eng = AlertEngine(container)

    twin_state = {
        "predictions": {
            "disease_probability": {
                "disease": "Wheat Rust",
                "probability": 0.45
            }
        },
        "risks": {
            "crop_failure_risk": 0.65
        },
        "profile": {
            "budget_spent": 90000.0,
            "budget_limit": 100000.0
        }
    }

    weather = {"has_warning": True, "warnings": ["Heatwave advisory"], "location": "Punjab"}
    market = {"crop": "Wheat", "trend": "bullish", "change_pct": 12.5}

    alerts = alert_eng.generate_alerts("farmer_autonomous_test_2", twin_state, weather, market)
    assert len(alerts) > 0
    # Weather hazard alert
    assert any("WEATHER WARNING" in a.message for a in alerts)
    # Disease risk alert
    assert any("DISEASE WARNING" in a.message for a in alerts)
    # Market opportunity price alert
    assert any("MARKET OPPORTUNITY" in a.message for a in alerts)
    # Budget overruns/crop failure financial risk
    assert any("FINANCIAL RISK" in a.message for a in alerts)


def test_notification_dispatched_and_history(temp_notif_db_path: str) -> None:
    """Verifies channel payload mappings (SMS, Voice, Dash, Push) and local log DB operations."""
    container = Container(settings)
    notif_eng = NotificationEngine(container, temp_notif_db_path)

    reminder = Reminder(
        farmer_id="farmer_test_notif",
        type="weather_alert",
        message="Drought advisory warning.",
        due_date=time.time() + 86400.0,
        priority="critical"
    )

    log = notif_eng.dispatch_notification("farmer_test_notif", reminder)

    # Check payload keys
    assert log["status"] == "delivered"
    assert "sms" in log
    assert "voice" in log
    assert "dashboard" in log
    assert "push" in log

    # Check template contents
    assert log["sms"]["body"].startswith("Kisan Mitra Alert")
    assert log["push"]["device_token"] == "token-farmer_test_notif"
    assert log["push"]["title"] == "New Agricultural Critical Event"

    # Verify log saved in history
    assert len(notif_eng.history) == 1
    assert notif_eng.history[0]["notification_id"] == f"NOTIF-{reminder.reminder_id}"


@pytest.mark.asyncio
async def test_orchestrator_autonomous_triggers() -> None:
    """Verifies that executing a query dynamically triggers the autonomous action monitoring cycle."""
    import uuid
    fid = f"farmer_auto_{uuid.uuid4().hex[:8]}"
    container = Container(settings)
    orchestrator = AgentOrchestrator(container)

    # Initial state: history should be empty for this farmer
    history_len_before = len(container.autonomous_manager.notification_engine.history)

    req = ExecutionRequest(
        query="Should I plant Wheat in Ludhiana next season?",
        session_id=fid,
        farmer_id=fid
    )

    res = await orchestrator.execute_query(req)
    assert res.status == "success"

    # Verify that a monitoring cycle was run and notification logs generated
    history_len_after = len(container.autonomous_manager.notification_engine.history)
    assert history_len_after > history_len_before
