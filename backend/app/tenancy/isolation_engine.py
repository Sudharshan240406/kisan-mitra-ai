import builtins
import logging
import os
from typing import Any

from .tenant_context import get_current_tenant_id
from .tenant_storage import TenantStorage

logger = logging.getLogger("kisan_mitra_ai.tenancy.isolation")

original_open = builtins.open

def tenant_aware_open(file: Any, mode: str = 'r', *args: Any, **kwargs: Any) -> Any:
    """
    Patched standard open routing calls targeting the standard database folder to tenant workspaces.
    """
    if isinstance(file, str) and ("data/" in file or "data\\" in file):
        tenant_id = get_current_tenant_id()
        if tenant_id:
            resolved_path = TenantStorage.get_tenant_path(file, tenant_id)
            dir_name = os.path.dirname(resolved_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            return original_open(resolved_path, mode, *args, **kwargs)
    return original_open(file, mode, *args, **kwargs)

class TenantIsolatedDictDescriptor:
    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:
            return self
        if not hasattr(instance, "_tenant_stores"):
            instance._tenant_stores = {}
        tenant_id = get_current_tenant_id() or "default"
        if not hasattr(instance, "_initialized_tenants"):
            instance._initialized_tenants = set()

        attr_stores = instance._tenant_stores.setdefault(self.name, {})
        if tenant_id not in attr_stores:
            attr_stores[tenant_id] = {}
            if tenant_id not in instance._initialized_tenants:
                instance._initialized_tenants.add(tenant_id)
                if hasattr(instance, "load_from_disk"):
                    try:
                        instance.load_from_disk()
                    except Exception as e:
                        logger.error(f"Error loading tenant disk state for {owner.__name__}: {e}")
        return attr_stores[tenant_id]

    def __set__(self, instance: Any, value: Any) -> None:
        if not hasattr(instance, "_tenant_stores"):
            instance._tenant_stores = {}
        tenant_id = get_current_tenant_id() or "default"
        attr_stores = instance._tenant_stores.setdefault(self.name, {})
        attr_stores[tenant_id] = value

class TenantIsolatedListDescriptor:
    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:
            return self
        if not hasattr(instance, "_tenant_stores"):
            instance._tenant_stores = {}
        tenant_id = get_current_tenant_id() or "default"
        if not hasattr(instance, "_initialized_tenants"):
            instance._initialized_tenants = set()

        attr_stores = instance._tenant_stores.setdefault(self.name, {})
        if tenant_id not in attr_stores:
            attr_stores[tenant_id] = []
            if tenant_id not in instance._initialized_tenants:
                instance._initialized_tenants.add(tenant_id)
                if hasattr(instance, "load_from_disk"):
                    try:
                        instance.load_from_disk()
                    except Exception as e:
                        logger.error(f"Error loading tenant disk state for {owner.__name__}: {e}")
        return attr_stores[tenant_id]

    def __set__(self, instance: Any, value: Any) -> None:
        if not hasattr(instance, "_tenant_stores"):
            instance._tenant_stores = {}
        tenant_id = get_current_tenant_id() or "default"
        attr_stores = instance._tenant_stores.setdefault(self.name, {})
        attr_stores[tenant_id] = value

class TenantIsolatedValueDescriptor:
    def __init__(self, name: str, default_value: Any = None) -> None:
        self.name = name
        self.default_value = default_value

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:
            return self
        if not hasattr(instance, "_tenant_stores"):
            instance._tenant_stores = {}
        tenant_id = get_current_tenant_id() or "default"
        attr_stores = instance._tenant_stores.setdefault(self.name, {})
        if tenant_id not in attr_stores:
            attr_stores[tenant_id] = self.default_value
        return attr_stores[tenant_id]

    def __set__(self, instance: Any, value: Any) -> None:
        if not hasattr(instance, "_tenant_stores"):
            instance._tenant_stores = {}
        tenant_id = get_current_tenant_id() or "default"
        attr_stores = instance._tenant_stores.setdefault(self.name, {})
        attr_stores[tenant_id] = value

class IsolationEngine:
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return

        # 1. Patch native builtins.open
        builtins.open = tenant_aware_open

        # 2. Patch target class descriptors dynamically
        from app.personalization.platform import PersonalizationPlatform
        PersonalizationPlatform.profiles = TenantIsolatedDictDescriptor("profiles")
        PersonalizationPlatform.twins = TenantIsolatedDictDescriptor("twins")
        PersonalizationPlatform.memories = TenantIsolatedDictDescriptor("memories")
        PersonalizationPlatform.consents = TenantIsolatedDictDescriptor("consents")
        PersonalizationPlatform.reminders = TenantIsolatedDictDescriptor("reminders")

        from app.digital_twin.twin_manager import TwinManager
        TwinManager.predictive_twins = TenantIsolatedDictDescriptor("predictive_twins")

        from app.learning.feedback_store import FeedbackStore
        FeedbackStore.recommendations = TenantIsolatedListDescriptor("recommendations")
        FeedbackStore.knowledge = TenantIsolatedListDescriptor("knowledge")
        FeedbackStore.agents = TenantIsolatedListDescriptor("agents")

        from app.observability.metrics_engine import MetricsEngine
        MetricsEngine._metrics = TenantIsolatedDictDescriptor("_metrics")

        from app.observability.tracing_engine import TracingEngine
        TracingEngine._spans = TenantIsolatedListDescriptor("_spans")

        from app.workflows.queue_manager import QueueManager
        QueueManager.jobs = TenantIsolatedDictDescriptor("jobs")

        from app.knowledge.vector_store import (
            ChromaVectorStore,
            FAISSVectorStore,
            QdrantVectorStore,
        )
        FAISSVectorStore.documents = TenantIsolatedListDescriptor("documents")
        ChromaVectorStore.documents = TenantIsolatedListDescriptor("documents")
        QdrantVectorStore.documents = TenantIsolatedListDescriptor("documents")

        from app.governance.audit_manager import AuditManager
        AuditManager.records = TenantIsolatedListDescriptor("records")

        from app.performance.cache_engine import CacheEngine
        CacheEngine._cache = TenantIsolatedDictDescriptor("_cache")

        from app.performance.performance_manager import PerformanceManager
        PerformanceManager.latencies = TenantIsolatedListDescriptor("latencies")
        PerformanceManager.throughput_count = TenantIsolatedValueDescriptor("throughput_count", 0)

        cls._initialized = True
        logger.info("[IsolationEngine] Multi-tenant dynamic boundaries initialized successfully.")
