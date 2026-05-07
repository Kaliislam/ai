from turkish_jarvis.agents.base_agent import BaseAgent


class ReminderManagerAgent(BaseAgent):
    """Hatırlatma Yöneticisi — reminders, alerts, deadlines, recurring_tasks."""

    def __init__(self):
        super().__init__("remindermanager", "Hatırlatma Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["reminders", "alerts", "deadlines", "recurring_tasks"]

    async def _process(self, task, llm_client=None):
        return {"agent": "remindermanager", "processed": task.get("count", 0)}
