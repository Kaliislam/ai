from turkish_jarvis.agents.base_agent import BaseAgent


class KnowledgeManagerAgent(BaseAgent):
    """Bilgi Yöneticisi — knowledge_base, faq, retrieval, indexing."""

    def __init__(self):
        super().__init__("knowledgemanager", "Bilgi Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["knowledge_base", "faq", "retrieval", "indexing"]

    async def _process(self, task, llm_client=None):
        return {"agent": "knowledgemanager", "processed": task.get("count", 0)}
