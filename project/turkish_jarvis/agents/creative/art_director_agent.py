"""ArtDirector Agent — görsel kimlik ve estetik yönetimi."""

from turkish_jarvis.agents.base_agent import BaseAgent

class ArtDirectorAgent(BaseAgent):
    """Sanat yönetmeni ajanı — görsel kimlik ve estetik yönetimi."""
    def __init__(self):
        super().__init__("ArtDirector", "Art Director", "Creative", "gemma4:latest")
        self.skills = ["art direction", "visual identity", "aesthetic", "brand visuals", "design systems"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by ArtDirector", "type": task.get("type", "generic")}
