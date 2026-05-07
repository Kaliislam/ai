from turkish_jarvis.agents.base_agent import BaseAgent


class DietManagerAgent(BaseAgent):
    """Diyet Yöneticisi — meal_planning, nutrition, calories, macros."""

    def __init__(self):
        super().__init__("dietmanager", "Diyet Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["meal_planning", "nutrition", "calories", "macros"]

    async def _process(self, task, llm_client=None):
        return {"agent": "dietmanager", "processed": task.get("count", 0)}
