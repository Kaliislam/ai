from turkish_jarvis.agents.base_agent import BaseAgent


class BudgetManagerAgent(BaseAgent):
    """Bütçe Yöneticisi — budgeting, expense_tracking, saving, goals, forecasting."""

    def __init__(self):
        super().__init__("budgetmanager", "Bütçe Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["budgeting", "expense_tracking", "saving", "goals", "forecasting"]

    async def _process(self, task, llm_client=None):
        return {"agent": "budgetmanager", "processed": task.get("count", 0)}
