"""Performance Agent — Performans ajanı."""

from turkish_jarvis.agents.base_agent import BaseAgent


class PerformanceAgent(BaseAgent):
    """Performans ajanı — profil çıkarma, bottleneck analizi, optimizasyon."""

    def __init__(self):
        super().__init__("Performance", "Performance Engineer", "Systems", "qwen3-coder:30b")
        self.skills = ["profiling", "bottleneck", "optimization", "load_test"]

    async def _process(self, task, llm_client=None):
        return {"performance_report": "generated", "action_taken": task.get("action")}
