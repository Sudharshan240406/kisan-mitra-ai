from app.core.context import AgentContext
from app.tools.scheme_tool import GovernmentSchemeTool


class GovernmentSchemeService:
    """
    Domain service encapsulating government subsidy schemes eligibility.
    """
    def __init__(self) -> None:
        self.scheme_tool = GovernmentSchemeTool()

    async def get_schemes_eligibility(self, farmer_id: str, context: AgentContext) -> str:
        """
        Coordinates querying government schemes, incorporating active integration details if configured.
        """
        container = context.metadata.get("container") if context else None
        if container and hasattr(container, "integration_registry"):
            active_adapter = container.integration_registry.get_active("government")
            if active_adapter:
                try:
                    result = await container.resilient_runner.execute(
                        integration_id=active_adapter.metadata.id,
                        operation_name="list_schemes",
                        func=lambda: active_adapter.list_schemes(),
                        trace_id=context.trace_id,
                        request_id=context.request_id,
                        session_id=context.session_id
                    )
                    schemes_text = "; ".join([f"{s.get('name')}: {s.get('benefit')} ({s.get('type')})" for s in result])
                    return (
                        f"Government Integration ({active_adapter.metadata.name}) output: "
                        f"Schemes retrieved: {schemes_text}."
                    )
                except Exception as e:
                    return f"Government Integration ({active_adapter.metadata.name}) failed: {e!s}. Falling back to default eligibility."

        return await self.scheme_tool.run({"farmer_id": farmer_id}, context)
