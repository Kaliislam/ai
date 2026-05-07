from turkish_jarvis.agents.base_agent import BaseAgent


class RecipeManagerAgent(BaseAgent):
    """Tarif Yöneticisi — recipes, ingredients, meal_prep, suggestions."""

    def __init__(self):
        super().__init__("recipemanager", "Tarif Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["recipes", "ingredients", "meal_prep", "suggestions"]

    async def _process(self, task, llm_client=None):
        return {"agent": "recipemanager", "processed": task.get("count", 0)}
