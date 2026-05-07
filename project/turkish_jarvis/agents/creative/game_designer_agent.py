"""GameDesigner Agent — mekanik ve seviye tasarımı."""

from turkish_jarvis.agents.base_agent import BaseAgent

class GameDesignerAgent(BaseAgent):
    """Oyun tasarımcısı ajanı — mekanik ve seviye tasarımı."""
    def __init__(self):
        super().__init__("GameDesigner", "Game Designer", "Creative", "gemma4:latest")
        self.skills = ["game mechanics", "level design", "narrative design", "balance", "playtesting"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by GameDesigner", "type": task.get("type", "generic")}
