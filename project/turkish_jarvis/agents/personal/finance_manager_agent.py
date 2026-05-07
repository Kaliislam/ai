from turkish_jarvis.agents.base_agent import BaseAgent


class FinanceManagerAgent(BaseAgent):
    """Finans Yöneticisi — financial_tracking, accounts, transactions, statements."""

    def __init__(self):
        super().__init__("financemanager", "Finans Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["financial_tracking", "accounts", "transactions", "statements"]

    async def _process(self, task, llm_client=None):
        return {"agent": "financemanager", "processed": task.get("count", 0)}
