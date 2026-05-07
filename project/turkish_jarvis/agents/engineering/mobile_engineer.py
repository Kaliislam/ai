from turkish_jarvis.agents.base_agent import BaseAgent


class MobileEngineer(BaseAgent):
    """Mobil geliştirici -- iOS ve Android uygulamalari."""

    def __init__(self):
        super().__init__("MobileDev", "Mobile Engineer", "Engineering")
        self.skills = ["flutter", "swift", "kotlin", "react_native", "push_notifications"]

    async def _process(self, task, llm_client=None):
        return {"action": "mobile_dev", "platform": task.get("platform")}
