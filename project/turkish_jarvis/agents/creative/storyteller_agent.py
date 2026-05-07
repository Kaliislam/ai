"""Storyteller Agent — öykü ve karakter geliştirme."""

from turkish_jarvis.agents.base_agent import BaseAgent

class StorytellerAgent(BaseAgent):
    """Hikaye anlatıcı ajanı — öykü ve karakter geliştirme."""
    def __init__(self):
        super().__init__("Storyteller", "Storyteller", "Creative", "gemma4:latest")
        self.skills = ["narrative", "character arcs", "worldbuilding", "plot design", "dialogue writing"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Storyteller", "type": task.get("type", "generic")}
