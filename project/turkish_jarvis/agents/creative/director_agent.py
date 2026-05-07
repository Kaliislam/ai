"""Director Agent — sahne ve performans yönetimi."""

from turkish_jarvis.agents.base_agent import BaseAgent

class DirectorAgent(BaseAgent):
    """Yönetmen ajanı — sahne ve performans yönetimi."""
    def __init__(self):
        super().__init__("Director", "Director", "Creative", "gemma4:latest")
        self.skills = ["direction", "casting", "visual storytelling", "blocking", "creative vision"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Director", "type": task.get("type", "generic")}
