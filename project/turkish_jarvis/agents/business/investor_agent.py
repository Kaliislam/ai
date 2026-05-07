"""Investor Agent — yatırım analizi ve portföy yönetimi."""

from turkish_jarvis.agents.base_agent import BaseAgent

class InvestorAgent(BaseAgent):
    """Yatırımcı ajanı — yatırım analizi ve portföy yönetimi."""
    def __init__(self):
        super().__init__("Investor", "Investor", "Business", "gemma4:latest")
        self.skills = ["investment analysis", "due diligence", "portfolio", "valuation", "risk assessment"]

    async def _process(self, task, llm_client=None):
        return {"content": "Processed by Investor", "type": task.get("type", "generic")}
