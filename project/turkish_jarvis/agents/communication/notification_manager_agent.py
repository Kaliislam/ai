from turkish_jarvis.agents.base_agent import BaseAgent


class NotificationManagerAgent(BaseAgent):
    """Bildirim Yöneticisi — notifications, push_email, digest, preferences."""

    def __init__(self):
        super().__init__("notificationmanager", "Bildirim Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["notifications", "push_email", "digest", "preferences"]

    async def _process(self, task, llm_client=None):
        return {"agent": "notificationmanager", "processed": task.get("count", 0)}
