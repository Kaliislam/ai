"""Sales Agent — satış hunisi ve kapanış."""

from turkish_jarvis.agents.base_agent import BaseAgent

class SalesAgent(BaseAgent):
    """Satış uzmanı ajanı — satış hunisi ve kapanış."""
    def __init__(self):
        super().__init__("Sales", "Sales", "Business", "gemma4:latest")
        self.skills = ["sales", "lead generation", "negotiation", "closing", "crm"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Sales", "type": task.get("type", "generic")}
