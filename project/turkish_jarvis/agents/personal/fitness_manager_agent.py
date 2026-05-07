from turkish_jarvis.agents.base_agent import BaseAgent


class FitnessManagerAgent(BaseAgent):
    """Fitness Yöneticisi — workout_plans, exercise_tracking, goals, routines."""

    def __init__(self):
        super().__init__("fitnessmanager", "Fitness Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["workout_plans", "exercise_tracking", "goals", "routines"]

    async def _process(self, task, llm_client=None):
        return {"agent": "fitnessmanager", "processed": task.get("count", 0)}
