from turkish_jarvis.agents.base_agent import BaseAgent


class FrontendEngineer(BaseAgent):
    """Frontend geliştirici -- kullanici arayüzü ve deneyim."""

    def __init__(self):
        super().__init__("FrontendDev", "Frontend Engineer", "Engineering")
        self.skills = ["react", "typescript", "tailwind", "nextjs", "ui_ux"]

    async def _process(self, task, llm_client=None):
        return {"action": "frontend_dev", "component": task.get("component")}
