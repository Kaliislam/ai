from turkish_jarvis.agents.base_agent import BaseAgent


class CultureExpertAgent(BaseAgent):
    """Kültür Uzmanı — culture_history, traditions, arts, heritage."""

    def __init__(self):
        super().__init__("cultureexpert", "Kültür Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["culture_history", "traditions", "arts", "heritage"]

    async def _process(self, task, llm_client=None):
        return {"agent": "cultureexpert", "processed": task.get("count", 0)}
