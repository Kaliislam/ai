"""Recruiter Agent — aday bulma ve değerlendirme."""

from turkish_jarvis.agents.base_agent import BaseAgent

class RecruiterAgent(BaseAgent):
    """İşe alım uzmanı ajanı — aday bulma ve değerlendirme."""
    def __init__(self):
        super().__init__("Recruiter", "Recruiter", "Business", "gemma4:latest")
        self.skills = ["recruiting", "sourcing", "interviewing", "assessment", "onboarding"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Recruiter", "type": task.get("type", "generic")}
