"""HR Agent — insan kaynakları politikaları."""

from turkish_jarvis.agents.base_agent import BaseAgent

class HRAgent(BaseAgent):
    """İK uzmanı ajanı — insan kaynakları politikaları."""
    def __init__(self):
        super().__init__("HR", "HR", "Business", "gemma4:latest")
        self.skills = ["hr policies", "compensation", "compliance", "employee relations", "culture"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by HR", "type": task.get("type", "generic")}
