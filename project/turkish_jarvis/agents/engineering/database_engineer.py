from turkish_jarvis.agents.base_agent import BaseAgent


class DatabaseEngineer(BaseAgent):
    """Veritabani mühendisi -- şema tasarimi, optimizasyon ve replikasyon."""

    def __init__(self):
        super().__init__("DBEng", "Database Engineer", "Engineering")
        self.skills = ["postgresql", "mongodb", "redis", "sharding", "indexing"]

    async def _process(self, task, llm_client=None):
        return {"action": "db_design", "schema": task.get("schema")}
