"""Photographer Agent — fotoğraf çekimi ve düzenleme."""

from turkish_jarvis.agents.base_agent import BaseAgent

class PhotographerAgent(BaseAgent):
    """Fotoğrafçı ajanı — fotoğraf çekimi ve düzenleme."""
    def __init__(self):
        super().__init__("Photographer", "Photographer", "Creative", "gemma4:latest")
        self.skills = ["photography", "photo editing", "lighting", "composition", "portrait"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Photographer", "type": task.get("type", "generic")}
