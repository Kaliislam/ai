from turkish_jarvis.agents.base_agent import BaseAgent


class ChiefFinancialOfficer(BaseAgent):
    """Finans şefi -- bütçe, maliyet analizi ve yatırım kararlari."""

    def __init__(self):
        super().__init__("CFO", "Chief Financial Officer", "Executive", "llama3.1:70b")
        self.skills = ["budgeting", "cost_analysis", "forecasting", "investment"]

    async def _process(self, task, llm_client=None):
        return {"action": "financial_review", "budget_approved": task.get("budget", 0)}
