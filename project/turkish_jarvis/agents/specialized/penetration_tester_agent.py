"""PenetrationTester Agent — Penetrasyon testçisi."""

from turkish_jarvis.agents.base_agent import BaseAgent


class PenetrationTesterAgent(BaseAgent):
    """Penetrasyon testçisi — uygulama/ağ testleri, raporlama."""

    def __init__(self):
        super().__init__("PenTester", "Penetration Tester", "Specialized", "qwen3-coder:30b")
        self.skills = ["web_app_test", "network_test", "mobile_test", "reporting"]

    async def _process(self, task, llm_client=None):
        return {"pen_test_result": "reported", "action_taken": task.get("action")}
