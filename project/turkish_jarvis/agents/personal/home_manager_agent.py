from turkish_jarvis.agents.base_agent import BaseAgent


class HomeManagerAgent(BaseAgent):
    """Ev Yöneticisi — home_maintenance, chores, inventory, cleaning."""

    def __init__(self):
        super().__init__("homemanager", "Ev Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["home_maintenance", "chores", "inventory", "cleaning"]

    async def _process(self, task, llm_client=None):
        return {"agent": "homemanager", "processed": task.get("count", 0)}
