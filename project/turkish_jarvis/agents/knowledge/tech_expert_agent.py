from turkish_jarvis.agents.base_agent import BaseAgent


class TechExpertAgent(BaseAgent):
    """Teknoloji Uzmanı — technology_trends, gadgets, software, innovation."""

    def __init__(self):
        super().__init__("techexpert", "Teknoloji Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["technology_trends", "gadgets", "software", "innovation"]

    async def _process(self, task, llm_client=None):
        return {"agent": "techexpert", "processed": task.get("count", 0)}
