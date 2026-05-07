from turkish_jarvis.agents.base_agent import BaseAgent


class SearchManagerAgent(BaseAgent):
    """Arama Yöneticisi — search, indexing, ranking, query_optimization."""

    def __init__(self):
        super().__init__("searchmanager", "Arama Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["search", "indexing", "ranking", "query_optimization"]

    async def _process(self, task, llm_client=None):
        return {"agent": "searchmanager", "processed": task.get("count", 0)}
