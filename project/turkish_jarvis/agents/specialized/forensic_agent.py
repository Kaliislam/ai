"""Forensic Agent — Adli bilişim uzmanı."""

from turkish_jarvis.agents.base_agent import BaseAgent


class ForensicAgent(BaseAgent):
    """Adli bilişim uzmanı — disk imajı, timeline analizi, kanıt zinciri."""

    def __init__(self):
        super().__init__("Forensic", "Digital Forensic Specialist", "Specialized", "qwen3-coder:30b")
        self.skills = ["disk_imaging", "timeline", "chain_of_custody", "e-discovery"]

    async def _process(self, task, llm_client=None):
        return {"forensic_report": "compiled", "action_taken": task.get("action")}
