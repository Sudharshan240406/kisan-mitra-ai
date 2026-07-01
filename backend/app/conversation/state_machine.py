import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from app.conversation.context import ConversationContext

logger = logging.getLogger("kisan_mitra_ai.conversation")


class ConversationState(ABC):
    """
    Abstract Base Class for all Conversation Machine States.
    """
    @property
    @abstractmethod
    def state_name(self) -> str:
        pass

    @abstractmethod
    async def on_entry(self, context: ConversationContext) -> bool:
        pass

    @abstractmethod
    async def validate(self, context: ConversationContext) -> bool:
        pass

    @abstractmethod
    async def execute(self, context: ConversationContext) -> Optional[str]:
        pass

    @abstractmethod
    async def on_exit(self, context: ConversationContext) -> bool:
        pass

    @abstractmethod
    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        pass


# 1. Greeting
class GreetingState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Greeting"

    async def on_entry(self, context: ConversationContext) -> bool:
        logger.info(f"[{context.conversation_id}] Entry Greeting State.")
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # Simulate moving to intent identification next
        return "Intent Identification"

    async def on_exit(self, context: ConversationContext) -> bool:
        logger.info(f"[{context.conversation_id}] Exit Greeting State.")
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 2. Intent Identification
class IntentIdentificationState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Intent Identification"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # If crop/query metadata implies intent, move forward
        return "Context Collection"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 3. Context Collection
class ContextCollectionState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Context Collection"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # Check if crop symptoms are missing
        if not context.metadata.get("crop"):
            return "Missing Information Collection"
        return "Capability Selection"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 4. Missing Information Collection
class MissingInformationCollectionState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Missing Information Collection"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # Wait for replenishment or simulate collect
        context.metadata["crop"] = "Wheat"  # Simulated replenishment
        return "Capability Selection"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 5. Capability Selection
class CapabilitySelectionState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Capability Selection"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        context.current_capability = "disease_diagnosis"
        return "Workflow Selection"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 6. Workflow Selection
class WorkflowSelectionState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Workflow Selection"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        context.current_workflow = "disease_workflow"
        return "Reasoning"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 7. Reasoning
class ReasoningState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Reasoning"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # Simulates worker agent runs
        return "Policy Validation"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 8. Policy Validation
class PolicyValidationState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Policy Validation"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        return "Recommendation Generation"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 9. Recommendation Generation
class RecommendationGenerationState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Recommendation Generation"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        return "Recommendation Confirmation"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 10. Recommendation Confirmation
class RecommendationConfirmationState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Recommendation Confirmation"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        return "Follow-up Planning"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 11. Follow-up Planning
class FollowUpPlanningState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Follow-up Planning"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        return "Conversation Closure"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 12. Conversation Closure
class ConversationClosureState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Conversation Closure"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # Stop machine processing loop
        return None

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Error Recovery"


# 13. Error Recovery
class ErrorRecoveryState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Error Recovery"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # Return to safety loop close
        return "Conversation Closure"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Escalation"


# 14. Escalation
class EscalationState(ConversationState):
    @property
    def state_name(self) -> str:
        return "Escalation"

    async def on_entry(self, context: ConversationContext) -> bool:
        return True

    async def validate(self, context: ConversationContext) -> bool:
        return True

    async def execute(self, context: ConversationContext) -> Optional[str]:
        # Escalates context status
        context.metadata["escalation_triggered"] = True
        return "Conversation Closure"

    async def on_exit(self, context: ConversationContext) -> bool:
        return True

    async def handle_error(self, error: Exception, context: ConversationContext) -> str:
        return "Conversation Closure"


class ConversationStateMachine:
    """
    Deterministic transition supervisor overseeing ConversationState implementations.
    """
    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}
        self._register_default_states()

    def register_state(self, state: ConversationState) -> None:
        """
        Dynamically registers custom states into the machine.
        """
        self._states[state.state_name] = state

    async def transition_to(self, context: ConversationContext, target_state: str, reason: str = "Transition") -> None:
        """
        Transitions the conversation state context safely.
        """
        current = self._states.get(context.current_state)
        target = self._states.get(target_state)

        if not target:
            raise ValueError(f"Target state '{target_state}' is not registered.")

        if current:
            await current.on_exit(context)

        from_state = context.current_state
        context.current_state = target_state
        context.timeline.append({
            "from_state": from_state,
            "to_state": target_state,
            "timestamp": time.time(),
            "reason": reason
        })

        await target.on_entry(context)

    async def process_step(self, context: ConversationContext) -> Optional[str]:
        """
        Processes a single step in the active state execution loop.
        Returns the new state name, or None if the machine is paused.
        """
        state = self._states.get(context.current_state)
        if not state:
            raise KeyError(f"State '{context.current_state}' not registered.")

        try:
            is_valid = await state.validate(context)
            if not is_valid:
                # Move to error recovery
                await self.transition_to(context, "Error Recovery", "Validation Failed")
                return "Error Recovery"

            next_state = await state.execute(context)
            if next_state:
                await self.transition_to(context, next_state, "Execution Transition")
                return next_state
            return None

        except Exception as e:
            recovery_state = await state.handle_error(e, context)
            await self.transition_to(context, recovery_state, f"Error: {e!s}")
            return recovery_state

    def _register_default_states(self) -> None:
        self.register_state(GreetingState())
        self.register_state(IntentIdentificationState())
        self.register_state(ContextCollectionState())
        self.register_state(MissingInformationCollectionState())
        self.register_state(CapabilitySelectionState())
        self.register_state(WorkflowSelectionState())
        self.register_state(ReasoningState())
        self.register_state(PolicyValidationState())
        self.register_state(RecommendationGenerationState())
        self.register_state(RecommendationConfirmationState())
        self.register_state(FollowUpPlanningState())
        self.register_state(ConversationClosureState())
        self.register_state(ErrorRecoveryState())
        self.register_state(EscalationState())
