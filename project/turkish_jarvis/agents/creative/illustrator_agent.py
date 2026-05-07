"""Illustrator Agent — görsel tasarım ve çizim."""

from turkish_jarvis.agents.base_agent import BaseAgent

class IllustratorAgent(BaseAgent):
    """İllüstratör ajanı — görsel tasarım ve çizim."""
    def __init__(self):
        super().__init__("Illustrator", "Illustrator", "Creative", "gemma4:latest")
        self.skills = ["illustration", "digital art", "sketching", "concept art", "visual design"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Illustrator", "type": task.get("type", "generic")}
