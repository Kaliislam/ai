from turkish_jarvis.agents.base_agent import BaseAgent


class TravelManagerAgent(BaseAgent):
    """Seyahat Yöneticisi — travel_planning, bookings, itineraries, packing."""

    def __init__(self):
        super().__init__("travelmanager", "Seyahat Yöneticisi", "Personal", "gemma4:latest")
        self.skills = ["travel_planning", "bookings", "itineraries", "packing"]

    async def _process(self, task, llm_client=None):
        return {"agent": "travelmanager", "processed": task.get("count", 0)}
