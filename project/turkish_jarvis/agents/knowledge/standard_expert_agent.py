from turkish_jarvis.agents.base_agent import BaseAgent


class StandardExpertAgent(BaseAgent):
    """Standart Uzmanı — standards_iso, compliance, certification, requirements."""

    def __init__(self):
        super().__init__("standardexpert", "Standart Uzmanı", "Knowledge", "gemma4:latest")
        self.skills = ["standards_iso", "compliance", "certification", "requirements"]

    async def _process(self, task, llm_client=None):
        return {"agent": "standardexpert", "processed": task.get("count", 0)}
