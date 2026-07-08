import json
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Optional

from agents.disease.disease import KnowledgeAgent
from agents.market.market import MarketAgent
from agents.memory.memory import MemoryAgent

# Core Framework Agent Imports
from agents.planner.planner import PlannerAgent
from agents.schemes.schemes import GovernmentSchemeAgent
from agents.verifier.verifier import VerifierAgent
from agents.weather.weather import WeatherAgent
from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.channels import router as channels_router
from app.api.v1.demo import router as demo_router
from app.api.v1.health import router as health_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.media import router as media_router
from app.api.v1.observability import router as observability_router
from app.api.v1.personalization import router as personalization_router
from app.api.v1.security import router as security_router
from app.api.v1.sms import router as sms_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.telephony import router as telephony_router
from app.api.v1.websocket import router as websocket_router
from app.core.config import settings, validate_production_config
from app.core.container import Container
from app.core.exceptions import KisanMitraException
from app.core.logging_config import setup_logging
from app.dependencies.container import get_container
from app.middleware.error_handler import (
    general_exception_handler,
    http_exception_handler,
    kisan_mitra_exception_handler,
    validation_exception_handler,
)
from app.orchestrator.orchestrator import AgentOrchestrator
from app.schemas.requests import ExecutionRequest
from app.schemas.responses import HealthResponse, StandardResponse
from app.security.security_manager import (
    PermissionRequirement,
    RoleRequirement,
    bearer_scheme,
)
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Setup centralized logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Enforce production security configuration validation
    validate_production_config(settings)

    # Initialize DI Container
    logger.info(f"Starting {settings.APP_NAME} in environment: {settings.APP_ENV}")
    container = Container(settings)

    # 1. Instantiate agents
    planner_agent = PlannerAgent(container.llm_provider)
    weather_agent = WeatherAgent(container.llm_provider, container.weather_service)
    market_agent = MarketAgent(container.llm_provider, container.market_service)
    memory_agent = MemoryAgent(container.llm_provider, container.memory_service)
    knowledge_agent = KnowledgeAgent(container.llm_provider, container.knowledge_service)
    scheme_agent = GovernmentSchemeAgent(container.llm_provider, container.scheme_service)
    verifier_agent = VerifierAgent(container.llm_provider)

    # 2. Initialize agents
    await planner_agent.initialize()
    await weather_agent.initialize()
    await market_agent.initialize()
    await memory_agent.initialize()
    await knowledge_agent.initialize()
    await scheme_agent.initialize()
    await verifier_agent.initialize()

    # 3. Register agents in the registry
    container.registry.register(planner_agent)
    container.registry.register(weather_agent)
    container.registry.register(market_agent)
    container.registry.register(memory_agent)
    container.registry.register(knowledge_agent)
    container.registry.register(scheme_agent)
    container.registry.register(verifier_agent)

    # Bind container to app state
    app.state.container = container

    # Start background workflows
    container.workflow_manager.start()

    yield

    # Stop background workflows
    await container.workflow_manager.stop()

    # Cleanup agents
    logger.info("Cleaning up agent resources...")
    for agent_name in container.registry.list_agents():
        agent = container.registry.get(agent_name)
        await agent.cleanup()

    logger.info(f"Shutting down {settings.APP_NAME}")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade multi-agent agricultural advisory platform backend.",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure API Response Compression (gzip)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure Custom Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable[[Request], Any]) -> Any:
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' http://localhost:8000 http://localhost "
        "ws://localhost:8000 ws://localhost wss://localhost:8000 wss://localhost;"
    )
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

# Register Centralized Exception Handlers
app.add_exception_handler(KisanMitraException, kisan_mitra_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Register routers
app.include_router(channels_router)
app.include_router(media_router)
app.include_router(telephony_router)
app.include_router(sms_router)
app.include_router(telemetry_router)
app.include_router(integrations_router)
app.include_router(knowledge_router)
app.include_router(health_router, prefix="/api/v1/health", tags=["Health"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Platform"])
app.include_router(personalization_router)
app.include_router(security_router)
app.include_router(admin_router, dependencies=[Depends(RoleRequirement("Admin"))])
app.include_router(websocket_router)
app.include_router(demo_router)
app.include_router(observability_router, dependencies=[Depends(PermissionRequirement("api:observability"))])



@app.get("/", tags=["General"])
async def root() -> dict[str, str]:
    """
    Root API endpoint welcome message.
    """
    return {
        "message": f"Welcome to the {settings.APP_NAME} API Service.",
        "environment": settings.APP_ENV,
        "status": "active"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health(container: Container = Depends(get_container)) -> HealthResponse:
    """
    Health check endpoint reporting systems and runtime agent checks.
    """
    orchestrator = AgentOrchestrator(container)
    orchestrator_health = orchestrator.health()

    components_status = {
        "database": "connected (mocked)",
        "cache": "connected (mocked)",
        "vector_db": "connected (mocked)",
        "agent_registry": ", ".join(container.registry.list_agents()),
        "event_bus": json.dumps(orchestrator_health["event_bus"]),
        "scheduler": json.dumps(orchestrator_health["scheduler"]),
        "metrics": json.dumps(orchestrator_health["metrics"])
    }

    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        components=components_status
    )

@app.post("/api/v1/query", response_model=StandardResponse, tags=["Orchestration"])
async def query(
    request: ExecutionRequest,
    container: Container = Depends(get_container),
    credentials: Optional[Any] = Depends(bearer_scheme)
) -> StandardResponse:
    """
    Execute user query through the multi-agent orchestration framework.
    """
    if credentials:
        try:
            security_mgr = getattr(container, "security_manager", None)
            if security_mgr:
                claims = security_mgr.verify_request_token(credentials.credentials)
                request.user_id = claims.get("sub")
                request.user_role = claims.get("role")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {e!s}"
            )

    orchestrator = AgentOrchestrator(container)
    return await orchestrator.execute_query(request)
