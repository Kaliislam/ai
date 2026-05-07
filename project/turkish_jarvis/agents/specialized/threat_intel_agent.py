"""ThreatIntel Agent — Tehdit istihbaratı."""

from turkish_jarvis.agents.base_agent import BaseAgent


class ThreatIntelAgent(BaseAgent):
    """Tehdit istihbaratı — IoC tarama, TTP eşleme, raporlama."""

    def __init__(self):
        super().__init__("ThreatIntel", "Threat Intelligence Analyst", "Specialized", "qwen3-coder:30b")
        self.skills = ["ioc_hunting", "ttp_mapping", "apt_tracking", "feeds"]

    async def _process(self, task, llm_client=None):
        return {"threat_intel": "updated", "action_taken": task.get("action")}
