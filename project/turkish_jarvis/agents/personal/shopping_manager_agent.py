from turkish_jarvis.agents.base_agent import BaseAgent


class ShoppingManagerAgent(BaseAgent):
    """Alışveriş Yöneticisi — shopping_lists, price_comparison, deals, tracking."""

    def __init__(self):
        super().__init__("shoppingmanager", "Alışveriş Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["shopping_lists", "price_comparison", "deals", "tracking"]

    async def _process(self, task, llm_client=None):
        return {"agent": "shoppingmanager", "processed": task.get("count", 0)}
