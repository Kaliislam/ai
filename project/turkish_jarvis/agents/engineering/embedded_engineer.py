from turkish_jarvis.agents.base_agent import BaseAgent


class EmbeddedEngineer(BaseAgent):
    """Gömülü sistem mühendisi -- donanim-yazilim entegrasyonu."""

    def __init__(self):
        super().__init__("EmbeddedDev", "Embedded Engineer", "Engineering")
        self.skills = ["c", "cpp", "rtos", "arduino", "iot_protocols"]

    async def _process(self, task, llm_client=None):
        return {"action": "firmware_dev", "device": task.get("device")}
