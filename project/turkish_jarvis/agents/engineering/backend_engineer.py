from turkish_jarvis.agents.base_agent import BaseAgent


class BackendEngineer(BaseAgent):
    """Backend geliştirici -- sunucu tarafi mantik ve API'ler."""

    def __init__(self):
        super().__init__("BackendDev", "Backend Engineer", "Engineering")
        self.skills = ["python", "fastapi", "django", "microservices", "redis"]

    async def _process(self, task, llm_client=None):
        return {"action": "backend_dev", "endpoint": task.get("endpoint")}
