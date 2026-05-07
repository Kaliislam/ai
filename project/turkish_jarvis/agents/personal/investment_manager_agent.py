from turkish_jarvis.agents.base_agent import BaseAgent


class InvestmentManagerAgent(BaseAgent):
    """Yatırım Yöneticisi — portfolio_tracking, stocks, bonds, risk_analysis."""

    def __init__(self):
        super().__init__("investmentmanager", "Yatırım Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["portfolio_tracking", "stocks", "bonds", "risk_analysis"]

    async def _process(self, task, llm_client=None):
        return {"agent": "investmentmanager", "processed": task.get("count", 0)}
