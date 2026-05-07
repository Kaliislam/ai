"""Entrepreneur Agent — fikir doğrulama ve MVP planlama."""

from turkish_jarvis.agents.base_agent import BaseAgent

class EntrepreneurAgent(BaseAgent):
    """Girişimci ajanı — fikir doğrulama ve MVP planlama."""
    def __init__(self):
        super().__init__("Entrepreneur", "Entrepreneur", "Business", "gemma4:latest")
        self.skills = ["ideation", "mvp planning", "market validation", "pitching", "lean startup"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Entrepreneur", "type": task.get("type", "generic")}
