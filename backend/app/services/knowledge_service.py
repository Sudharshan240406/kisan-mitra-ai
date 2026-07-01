from app.core.context import AgentContext
from app.tools.knowledge_tool import KnowledgeTool


class KnowledgeService:
    """
    Domain service encapsulating crop pathology manuals and tool execution coordinating.
    """
    def __init__(self) -> None:
        self.knowledge_tool = KnowledgeTool()

    async def get_pathology_advisory(self, crop: str, symptoms: list[str], context: AgentContext) -> str:
        """
        Coordinates querying pathology reference guides.
        """
        container = context.metadata.get("container") if context else None
        if container and hasattr(container, "knowledge_platform"):
            from app.knowledge.retrieval import KnowledgeRetrievalEngine
            engine = KnowledgeRetrievalEngine(container.knowledge_platform)
            query = f"{crop} {' '.join(symptoms)}"
            results = await engine.retrieve(query, limit=3, context=context)
            if results:
                advisories = []
                for res in results:
                    advisories.append(f"{res.get('title')}: {res.get('content')} (Source: {res.get('source')})")
                return "\n".join(advisories)

        return await self.knowledge_tool.run({"crop": crop, "symptoms": symptoms}, context)
