"""PR Agent — medya ilişkileri ve kriz yönetimi."""

from turkish_jarvis.agents.base_agent import BaseAgent

class PRAgent(BaseAgent):
    """Halkla ilişkiler ajanı — medya ilişkileri ve kriz yönetimi."""
    def __init__(self):
        super().__init__("PR", "PR", "Business", "gemma4:latest")
        self.skills = ["public relations", "media relations", "crisis management", "press releases", "reputation"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by PR", "type": task.get("type", "generic")}
