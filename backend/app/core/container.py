import logging
from typing import Any

from app.channels.channels import ChannelRegistry
from app.channels.router import ChannelRouter, ResponseRouter
from app.channels.sessions import SessionManager
from app.conversation.audit import DecisionAuditTrail
from app.conversation.clarification import ClarificationEngine
from app.conversation.context import ConversationContextManager
from app.conversation.escalation import HumanEscalationManager
from app.conversation.feedback import FeedbackEngine
from app.conversation.observability import ConversationMetricsTracker
from app.conversation.state_machine import ConversationStateMachine
from app.conversation.strategy import InteractionStrategyEngine, ResponseStrategyEngine
from app.core.ai.adapters import (
    ClaudeAdapter,
    GeminiAdapter,
    OllamaAdapter,
    OpenAIAdapter,
)
from app.core.ai.cost_manager import CostAndPerformanceManager
from app.core.ai.platform import AIModelPlatform
from app.core.ai.registry import AIProviderRegistry
from app.core.ai.router import AIModelRouter
from app.core.config import Settings, settings
from app.core.event_bus import EventBus
from app.core.feature_flags import FeatureFlags
from app.core.integrations.registry import IntegrationRegistry
from app.core.integrations.resilience import ResilientRunner
from app.core.llm_provider import BaseLLMProvider
from app.core.metrics import MetricsCollector
from app.core.telemetry import TelemetryFramework
from app.governance.benchmarks import BenchmarkRunner
from app.governance.engine import GovernanceEngine
from app.governance.models import ModelRegistry
from app.governance.plugins import PluginRegistry
from app.governance.prompts import PromptRegistry
from app.governance.validators import PlatformValidator
from app.intelligence.arm import AgriculturalReasoningMemory
from app.intelligence.policy import PolicyEngine

# Agricultural Knowledge Platform Imports
from app.knowledge.core import KnowledgePlatform
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.modules.crop import CropKnowledgeProvider
from app.knowledge.modules.disease import DiseaseKnowledgeProvider
from app.knowledge.modules.government import GovernmentKnowledgeProvider
from app.knowledge.modules.market import MarketKnowledgeProvider
from app.knowledge.modules.soil import SoilKnowledgeProvider
from app.knowledge.modules.weather import WeatherKnowledgeProvider
from app.knowledge.vector_store import (
    ChromaVectorStore,
    FAISSVectorStore,
    PineconeVectorStore,
    QdrantVectorStore,
)
from app.media.media import MediaProviderRegistry
from app.media.pipeline import MediaPipeline
from app.media.sessions import MediaSessionManager
from app.multimodal.core import MultimodalPlatform, VisionManager, VoiceManager
from app.multimodal.telemetry import MultimodalTelemetry
from app.orchestrator.capability import CapabilityRegistry
from app.orchestrator.registry import AgentRegistry

# Personalization Platform Imports
from app.personalization.platform import PersonalizationPlatform
from app.personalization.recommender import AdaptiveRecommendationEngine
from app.personalization.regional import RegionalIntelligenceService
from app.personalization.services import (
    ContinuousLearningService,
    DigitalTwinService,
    LongTermMemoryService,
    PrivacyConsentService,
    ProfileManagerService,
    ReminderSchedulerService,
)

# AI Reasoning & Decision Intelligence Platform Imports
from app.reasoning.chief import ChiefReasoningAgent
from app.reasoning.core import ReasoningPlatform
from app.reasoning.telemetry import ReasoningTelemetry
from app.services import (
    GovernmentSchemeService,
    KnowledgeService,
    MarketService,
    MemoryService,
    SoilService,
    WeatherService,
)
from app.sms.pipeline import SMSPipeline
from app.sms.sessions import SMSSessionManager
from app.sms.sms import SMSProviderRegistry
from app.sms.templates import SMSTemplateEngine
from app.telephony.ivr import IVRStateMachine
from app.telephony.manager import CallManager
from app.telephony.sessions import CallSessionManager
from app.telephony.telephony import TelephonyProviderRegistry
from app.voice.stt import (
    AzureSTTProvider,
    GoogleSTTProvider,
    LocalWhisperProvider,
    MockSTTProvider,
    STTProviderRegistry,
    WhisperSTTProvider,
)
from app.voice.tts import (
    AzureTTSProvider,
    CoquiTTSProvider,
    GoogleTTSProvider,
    MockTTSProvider,
    PiperTTSProvider,
    TTSProviderRegistry,
)

logger = logging.getLogger("kisan_mitra_ai")

class Container:
    """
    Dependency Injection Container that initializes and holds
    references to application services, database pools, caches,
    registries, event buses, and telemetry metrics collectors.
    """
    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        logger.info("Initializing DI Container...")

        # Event Bus, Metrics & Telemetry Exporter
        self.event_bus = EventBus()
        self.metrics = MetricsCollector()
        self.telemetry = TelemetryFramework()

        # AI Platform Core Infrastructure
        self.ai_registry = AIProviderRegistry()

        # Load and Register Provider Adapters
        self.ai_registry.register_adapter(
            "gemini-1.5-pro",
            GeminiAdapter(api_key=self.settings.GEMINI_API_KEY, model_name=self.settings.GEMINI_MODEL, temperature=self.settings.LLM_TEMPERATURE)
        )
        self.ai_registry.register_adapter(
            "gpt-4o",
            OpenAIAdapter(api_key=self.settings.OPENAI_API_KEY, model_name=self.settings.OPENAI_MODEL, temperature=self.settings.LLM_TEMPERATURE)
        )
        self.ai_registry.register_adapter(
            "claude-3-5-sonnet-latest",
            ClaudeAdapter(api_key=self.settings.CLAUDE_API_KEY, model_name=self.settings.CLAUDE_MODEL, temperature=self.settings.LLM_TEMPERATURE)
        )
        self.ai_registry.register_adapter(
            "llama3",
            OllamaAdapter(host=self.settings.OLLAMA_HOST, model_name=self.settings.OLLAMA_MODEL, temperature=self.settings.LLM_TEMPERATURE)
        )
        self.ai_registry.register_adapter(
            "groq-llama-3-70b",
            OpenAIAdapter(api_key=self.settings.OPENAI_API_KEY or "mock", model_name="groq-llama-3-70b", temperature=self.settings.LLM_TEMPERATURE, base_url="https://api.groq.com/openai/v1")
        )
        self.ai_registry.register_adapter(
            "openrouter-llama-3",
            OpenAIAdapter(api_key=self.settings.OPENAI_API_KEY or "mock", model_name="openrouter-llama-3", temperature=self.settings.LLM_TEMPERATURE, base_url="https://openrouter.ai/api/v1")
        )

        self.ai_cost_manager = CostAndPerformanceManager(self.ai_registry, daily_budget_usd=5.0)
        self.ai_router = AIModelRouter(self.ai_registry)

        # Wire unified AI model platform
        self.llm_provider: BaseLLMProvider = AIModelPlatform(
            registry=self.ai_registry,
            cost_manager=self.ai_cost_manager,
            router=self.ai_router,
            event_bus=self.event_bus,
            telemetry=self.telemetry
        )
        logger.info("Container: Dynamic AI Model Platform initialized successfully.")

        # Agent Registry
        self.registry = AgentRegistry()

        # Feature Flags & Policy Engine
        self.feature_flags = FeatureFlags(self.settings)
        self.policy_engine = PolicyEngine()

        # Capability Registry
        self.capability_registry = CapabilityRegistry()

        # Integration Platform Registry & Resilient Runner
        self.integration_registry = IntegrationRegistry(self.event_bus)
        self.resilient_runner = ResilientRunner(self.event_bus, self.telemetry)

        # Omnichannel Framework
        self.channel_registry = ChannelRegistry(self.event_bus)
        self.session_manager = SessionManager(self.event_bus)
        self.channel_router = ChannelRouter(self)
        self.response_router = ResponseRouter(self)


        # Agricultural Reasoning Memory (ARM)
        self.arm = AgriculturalReasoningMemory()

        # Agricultural Knowledge Platform
        self.knowledge_platform = KnowledgePlatform()
        self.knowledge_platform.manager.registry.register("government_schemes_db", GovernmentKnowledgeProvider())
        self.knowledge_platform.manager.registry.register("weather_advisories_db", WeatherKnowledgeProvider())
        self.knowledge_platform.manager.registry.register("market_prices_db", MarketKnowledgeProvider())
        self.knowledge_platform.manager.registry.register("crop_agronomy_manuals", CropKnowledgeProvider())
        self.knowledge_platform.manager.registry.register("soil_chemistry_manuals", SoilKnowledgeProvider())
        self.knowledge_platform.manager.registry.register("crop_pathology_manuals", DiseaseKnowledgeProvider())
        self.knowledge_platform.manager.registry.register("faiss", FAISSVectorStore())
        self.knowledge_platform.manager.registry.register("chroma", ChromaVectorStore(self.settings.CHROMA_DB_PATH))
        self.knowledge_platform.manager.registry.register("qdrant", QdrantVectorStore())
        self.knowledge_platform.manager.registry.register("pinecone", PineconeVectorStore())

        self.knowledge_graph = KnowledgeGraph()
        self._build_default_knowledge_graph()
        self.knowledge_platform.graph = self.knowledge_graph

        # AI Reasoning & Decision Intelligence Platform
        self.reasoning_platform = ReasoningPlatform()
        self.reasoning_telemetry = ReasoningTelemetry()
        self.reasoning_platform.registry.register("reasoning_telemetry", self.reasoning_telemetry)
        self.chief_agent = ChiefReasoningAgent(platform=self.reasoning_platform)
        logger.info("Container: AI Reasoning & Decision Intelligence Platform initialized.")

        # Domain Services
        self.weather_service = WeatherService()
        self.market_service = MarketService()
        self.knowledge_service = KnowledgeService()
        self.scheme_service = GovernmentSchemeService()
        self.memory_service = MemoryService(self.arm)
        self.soil_service = SoilService()

        # Conversation Intelligence Framework
        self.conversation_context_manager = ConversationContextManager()
        self.conversation_state_machine = ConversationStateMachine()
        self.interaction_strategy_engine = InteractionStrategyEngine()
        self.response_strategy_engine = ResponseStrategyEngine()
        self.clarification_engine = ClarificationEngine()
        self.decision_audit_trail = DecisionAuditTrail()
        self.human_escalation_manager = HumanEscalationManager()
        self.feedback_engine = FeedbackEngine()
        self.conversation_metrics_tracker = ConversationMetricsTracker()

        # Governance & Platform Integration
        self.plugin_registry = PluginRegistry()
        self.model_registry = ModelRegistry()
        self.prompt_registry = PromptRegistry()
        self.governance_engine = GovernanceEngine()

        # Media Intelligence Platform
        self.media_provider_registry = MediaProviderRegistry(self.event_bus, self.governance_engine)
        self.media_session_manager = MediaSessionManager(self.event_bus)
        self.stt_registry = STTProviderRegistry()
        self.tts_registry = TTSProviderRegistry()
        self._load_default_voice_providers()
        self.multimodal_platform = MultimodalPlatform(
            voice_manager=VoiceManager(self.stt_registry, self.tts_registry),
            vision_manager=VisionManager(self.media_provider_registry),
        )
        self.multimodal_telemetry = MultimodalTelemetry(self.telemetry, self.event_bus)
        self.media_pipeline = MediaPipeline(self)
        self._load_default_media_providers()

        # Telephony & IVR Platform
        self.telephony_provider_registry = TelephonyProviderRegistry(self.event_bus, self.governance_engine)
        self.call_session_manager = CallSessionManager(self.event_bus)
        self.ivr_state_machine = IVRStateMachine()
        self.call_manager = CallManager(self)
        self._load_default_telephony_providers()

        # SMS Intelligence Platform
        self.sms_provider_registry = SMSProviderRegistry(self.event_bus, self.governance_engine)
        self.sms_session_manager = SMSSessionManager(self.event_bus)
        self.sms_template_engine = SMSTemplateEngine()
        self.sms_pipeline = SMSPipeline(self)
        self._load_default_sms_providers()

        self.platform_validator = PlatformValidator()
        self.benchmark_runner = BenchmarkRunner.create_platform_benchmarks()

        # Load default integrations
        self._load_default_integrations()

        # Personalization Platform
        self.personalization_platform = PersonalizationPlatform()

        # Instantiate personalization services
        self.profile_manager_service = ProfileManagerService(self.personalization_platform)
        self.digital_twin_service = DigitalTwinService(self.personalization_platform)
        self.long_term_memory_service = LongTermMemoryService(self.personalization_platform)
        self.reminder_scheduler_service = ReminderSchedulerService(self.personalization_platform)
        self.continuous_learning_service = ContinuousLearningService(self.personalization_platform)
        self.privacy_consent_service = PrivacyConsentService(self.personalization_platform)
        self.regional_intelligence_service = RegionalIntelligenceService()
        self.adaptive_recommender = AdaptiveRecommendationEngine(self.personalization_platform)

        # Register personalization services
        self.personalization_platform.registry.register("profile_manager", self.profile_manager_service)
        self.personalization_platform.registry.register("digital_twin", self.digital_twin_service)
        self.personalization_platform.registry.register("long_term_memory", self.long_term_memory_service)
        self.personalization_platform.registry.register("reminder_scheduler", self.reminder_scheduler_service)
        self.personalization_platform.registry.register("continuous_learning", self.continuous_learning_service)
        self.personalization_platform.registry.register("privacy_consent", self.privacy_consent_service)
        self.personalization_platform.registry.register("regional_intelligence", self.regional_intelligence_service)
        self.personalization_platform.registry.register("adaptive_recommender", self.adaptive_recommender)
        logger.info("Container: Personalization Platform and Services initialized.")

        # Placeholders for future database/cache components
        self.db: Any | None = None
        self.cache: Any | None = None

        from app.learning.learning_manager import LearningManager
        self.learning_manager = LearningManager()

        from app.digital_twin.twin_manager import TwinManager
        self.twin_manager = TwinManager(self)

        from app.autonomous.autonomous_manager import AutonomousManager
        self.autonomous_manager = AutonomousManager(self)

        from app.observability import ObservabilityManager
        self.observability_manager = ObservabilityManager(self)

        from app.security import SecurityManager
        self.security_manager = SecurityManager(self)

        from app.workflows import WorkflowManager
        self.workflow_manager = WorkflowManager(self)

        from app.knowledge_pipeline import PipelineManager
        self.pipeline_manager = PipelineManager(self)

        from app.performance import PerformanceManager
        self.performance_manager = PerformanceManager(self)

        from app.tenancy.tenant_manager import TenantManager
        from app.tenancy.isolation_engine import IsolationEngine
        self.tenant_manager = TenantManager(self)
        IsolationEngine.initialize()

        from app.governance.governance_manager import GovernanceManager
        self.governance_manager = GovernanceManager(self)

        logger.info("Container services loaded successfully.")

    def _load_default_media_providers(self) -> None:
        """Loads and registers default mock media providers."""
        from app.media.media import (
            DocumentProvider,
            DroneImageProvider,
            ImageProvider,
            SensorProvider,
            VideoProvider,
            VoiceProvider,
        )
        self.media_provider_registry.register(VoiceProvider("voice-mock", "1.0.0", ["speech_to_text"]))
        self.media_provider_registry.register(ImageProvider("image-mock", "1.0.0", ["ocr", "disease_classification"]))
        self.media_provider_registry.register(DocumentProvider("doc-mock", "1.0.0", ["parsing"]))
        self.media_provider_registry.register(SensorProvider("sensor-mock", "1.0.0", ["anomaly_detection"]))
        self.media_provider_registry.register(DroneImageProvider("drone-mock", "1.0.0", ["ndvi_mapping"]))
        self.media_provider_registry.register(VideoProvider("video-mock", "1.0.0", ["frame_extraction"]))

    def _load_default_voice_providers(self) -> None:
        """Loads STT/TTS providers used by the multimodal platform."""
        self.stt_registry.register(MockSTTProvider())
        self.stt_registry.register(GoogleSTTProvider(api_key=self.settings.GEMINI_API_KEY))
        self.stt_registry.register(AzureSTTProvider())
        self.stt_registry.register(WhisperSTTProvider(api_key=self.settings.OPENAI_API_KEY))
        self.stt_registry.register(LocalWhisperProvider())

        self.tts_registry.register(MockTTSProvider())
        self.tts_registry.register(GoogleTTSProvider(api_key=self.settings.GEMINI_API_KEY))
        self.tts_registry.register(AzureTTSProvider())
        self.tts_registry.register(CoquiTTSProvider())
        self.tts_registry.register(PiperTTSProvider())

    def _load_default_telephony_providers(self) -> None:
        """Loads and registers default mock telephony adapters."""
        from app.telephony.telephony import (
            BSNLTelephonyProvider,
            ExotelTelephonyProvider,
            PlivoTelephonyProvider,
            TwilioTelephonyProvider,
        )
        self.telephony_provider_registry.register(
            TwilioTelephonyProvider("twilio-mock", "1.0.0", ["outbound_dialing", "tts"])
        )
        self.telephony_provider_registry.register(
            PlivoTelephonyProvider("plivo-mock", "1.0.0", ["outbound_dialing", "dtmf"])
        )
        self.telephony_provider_registry.register(
            ExotelTelephonyProvider("exotel-mock", "1.0.0", ["recording"])
        )
        self.telephony_provider_registry.register(
            BSNLTelephonyProvider("bsnl-mock", "1.0.0", ["sip_trunking"])
        )

    def _load_default_sms_providers(self) -> None:
        """Loads and registers default mock SMS adapters."""
        from app.sms.sms import (
            AWSSNSSMSProvider,
            BSNLSMSProvider,
            ExotelSMSProvider,
            GovSMSProvider,
            MSG91SMSProvider,
            TwilioSMSProvider,
        )
        self.sms_provider_registry.register(TwilioSMSProvider("twilio-sms-mock", "1.0.0", ["marketing_sms"]))
        self.sms_provider_registry.register(ExotelSMSProvider("exotel-sms-mock", "1.0.0", ["transactional_sms"]))
        self.sms_provider_registry.register(MSG91SMSProvider("msg91-sms-mock", "1.0.0", ["otp_sms"]))
        self.sms_provider_registry.register(AWSSNSSMSProvider("aws-sns-sms-mock", "1.0.0", ["bulk_sms"]))
        self.sms_provider_registry.register(BSNLSMSProvider("bsnl-sms-mock", "1.0.0", ["sip_sms"]))
        self.sms_provider_registry.register(GovSMSProvider("gov-sms-mock", "1.0.0", ["alerts_sms"]))

    def _load_default_integrations(self) -> None:
        """Loads and registers default external integration adapters."""
        from app.core.integrations.adapters.authentication import (
            LocalAuthAdapter,
            OAuthAdapter,
        )
        from app.core.integrations.adapters.government import (
            PMFBYAdapter,
            PMKisanAdapter,
            SoilHealthCardAdapter,
            StateSchemesAdapter,
        )
        from app.core.integrations.adapters.market import (
            AgmarknetMarketAdapter,
            eNAMMarketAdapter,
        )
        from app.core.integrations.adapters.notifications import (
            EmailNotificationAdapter,
            PushNotificationAdapter,
            SMSNotificationAdapter,
        )
        from app.core.integrations.adapters.storage import (
            CloudStorageAdapter,
            LocalStorageAdapter,
            PostgreSQLStorageAdapter,
            RedisStorageAdapter,
            VectorDBStorageAdapter,
        )
        from app.core.integrations.adapters.weather import (
            IMDWeatherAdapter,
            OpenWeatherAdapter,
            TomorrowIOWeatherAdapter,
        )

        # Register Weather Adapters
        self.integration_registry.register(IMDWeatherAdapter())
        self.integration_registry.register(OpenWeatherAdapter())
        self.integration_registry.register(TomorrowIOWeatherAdapter())

        # Register Market Adapters
        self.integration_registry.register(AgmarknetMarketAdapter())
        self.integration_registry.register(eNAMMarketAdapter())

        # Register Government Adapters
        self.integration_registry.register(PMKisanAdapter())
        self.integration_registry.register(PMFBYAdapter())
        self.integration_registry.register(SoilHealthCardAdapter())
        self.integration_registry.register(StateSchemesAdapter())

        # Register Storage Adapters
        self.integration_registry.register(LocalStorageAdapter())
        self.integration_registry.register(PostgreSQLStorageAdapter())
        self.integration_registry.register(RedisStorageAdapter())
        self.integration_registry.register(VectorDBStorageAdapter())
        self.integration_registry.register(CloudStorageAdapter())

        # Register Notifications Adapters
        self.integration_registry.register(SMSNotificationAdapter())
        self.integration_registry.register(EmailNotificationAdapter())
        self.integration_registry.register(PushNotificationAdapter())

        # Register Authentication Adapters
        self.integration_registry.register(LocalAuthAdapter())
        self.integration_registry.register(OAuthAdapter())

        # Register all default integration artifacts in Governance Ledger
        for integration in self.integration_registry.list_integrations():
            meta = integration.metadata
            self.governance_engine.register_artifact(
                artifact_type="integration",
                artifact_id=meta.id,
                version=meta.version,
                status=meta.status
            )

    def _build_default_knowledge_graph(self) -> None:
        """
        Builds the default ontology relationship graph connecting all agricultural entities.
        """
        graph = self.knowledge_graph
        # Nodes
        graph.add_node("state_punjab", "State", {"name": "Punjab"})
        graph.add_node("state_karnataka", "State", {"name": "Karnataka"})

        graph.add_node("dist_ludhiana", "District", {"name": "Ludhiana"})
        graph.add_node("dist_dharwad", "District", {"name": "Dharwad"})

        graph.add_node("vil_kila_raipur", "Village", {"name": "Kila Raipur"})
        graph.add_node("vil_heggeri", "Village", {"name": "Heggeri"})

        graph.add_node("farmer_ramesh", "Farmer", {"name": "Ramesh Singh"})
        graph.add_node("farmer_siddappa", "Farmer", {"name": "Siddappa Gowda"})

        graph.add_node("crop_wheat", "Crop", {"name": "Wheat"})
        graph.add_node("crop_rice", "Crop", {"name": "Rice"})

        graph.add_node("dis_wheat_rust", "Disease", {"name": "Wheat Rust"})
        graph.add_node("dis_rice_blast", "Disease", {"name": "Rice Blast"})

        graph.add_node("weather_monsoon_delay", "Weather", {"name": "Delayed Monsoon"})

        graph.add_node("mandi_ludhiana", "Market", {"name": "Ludhiana Mandi"})
        graph.add_node("mandi_bengaluru", "Market", {"name": "Bengaluru Yeshwanthpur Mandi"})

        graph.add_node("scheme_pm_kisan", "GovernmentScheme", {"name": "PM-Kisan"})
        graph.add_node("scheme_pmfby", "GovernmentScheme", {"name": "PMFBY"})

        graph.add_node("lang_punjabi", "Language", {"name": "Punjabi"})
        graph.add_node("lang_kannada", "Language", {"name": "Kannada"})

        # Edges
        graph.add_edge("dist_ludhiana", "state_punjab", "LOCATED_IN")
        graph.add_edge("dist_dharwad", "state_karnataka", "LOCATED_IN")

        graph.add_edge("vil_kila_raipur", "dist_ludhiana", "LOCATED_IN")
        graph.add_edge("vil_heggeri", "dist_dharwad", "LOCATED_IN")

        graph.add_edge("farmer_ramesh", "vil_kila_raipur", "LOCATED_IN")
        graph.add_edge("farmer_siddappa", "vil_heggeri", "LOCATED_IN")

        graph.add_edge("farmer_ramesh", "crop_wheat", "GROWING")
        graph.add_edge("farmer_siddappa", "crop_rice", "GROWING")

        graph.add_edge("crop_wheat", "dis_wheat_rust", "SUSCEPTIBLE_TO")
        graph.add_edge("crop_rice", "dis_rice_blast", "SUSCEPTIBLE_TO")

        graph.add_edge("weather_monsoon_delay", "crop_rice", "IMPACTS")

        graph.add_edge("crop_wheat", "mandi_ludhiana", "TRADED_AT")
        graph.add_edge("crop_rice", "mandi_bengaluru", "TRADED_AT")

        graph.add_edge("farmer_ramesh", "scheme_pm_kisan", "ELIGIBLE_FOR")
        graph.add_edge("farmer_siddappa", "scheme_pm_kisan", "ELIGIBLE_FOR")
        graph.add_edge("crop_wheat", "scheme_pmfby", "COVERED_BY")
        graph.add_edge("crop_rice", "scheme_pmfby", "COVERED_BY")

        graph.add_edge("state_punjab", "lang_punjabi", "SPOKEN_LANGUAGE")
        graph.add_edge("state_karnataka", "lang_kannada", "SPOKEN_LANGUAGE")
