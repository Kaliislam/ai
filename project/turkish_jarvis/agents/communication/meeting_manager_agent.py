from turkish_jarvis.agents.base_agent import BaseAgent


class MeetingManagerAgent(BaseAgent):
    """Toplantı Yöneticisi — meeting_scheduling, agendas, minutes, follow_up."""

    def __init__(self):
        super().__init__("meetingmanager", "Toplantı Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["meeting_scheduling", "agendas", "minutes", "follow_up"]

    async def _process(self, task, llm_client=None):
        return {"agent": "meetingmanager", "processed": task.get("count", 0)}
