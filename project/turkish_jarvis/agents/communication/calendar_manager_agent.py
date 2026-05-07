from turkish_jarvis.agents.base_agent import BaseAgent


class CalendarManagerAgent(BaseAgent):
    """Takvim Yöneticisi — calendar_scheduling, event_planning, availability, conflict_resolution."""

    def __init__(self):
        super().__init__("calendarmanager", "Takvim Yöneticisi", "Communication", "gemma4:latest")
        self.skills = ["calendar_scheduling", "event_planning", "availability", "conflict_resolution"]

    async def _process(self, task, llm_client=None):
        return {"agent": "calendarmanager", "processed": task.get("count", 0)}
