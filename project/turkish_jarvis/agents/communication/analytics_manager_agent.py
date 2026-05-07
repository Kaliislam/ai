from turkish_jarvis.agents.base_agent import BaseAgent


class AnalyticsManagerAgent(BaseAgent):
    """Analitik Yöneticisi — data_analysis, metrics, trends, insights."""

    def __init__(self):
        super().__init__("analyticsmanager", "Analitik Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["data_analysis", "metrics", "trends", "insights"]

    async def _process(self, task, llm_client=None):
        return {"agent": "analyticsmanager", "processed": task.get("count", 0)}
