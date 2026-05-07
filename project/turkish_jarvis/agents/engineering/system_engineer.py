from turkish_jarvis.agents.base_agent import BaseAgent


class SystemEngineer(BaseAgent):
    """Sistem mühendisi -- işletim sistemi, kernel ve düşük seviye optimizasyon."""

    def __init__(self):
        super().__init__("SysEng", "System Engineer", "Engineering")
        self.skills = ["linux", "kernel", "bash", "performance_tuning", "systemd"]

    async def _process(self, task, llm_client=None):
        return {"action": "system_config", "os": task.get("os")}
