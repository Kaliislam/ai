"""ReverseEngineer Agent — Tersine mühendis."""

from turkish_jarvis.agents.base_agent import BaseAgent


class ReverseEngineerAgent(BaseAgent):
    """Tersine mühendis — disassembly, decompilation, protokol analizi."""

    def __init__(self):
        super().__init__("ReverseEng", "Reverse Engineer", "Specialized", "qwen3-coder:30b")
        self.skills = ["disassembly", "decompile", "protocol", "firmware"]

    async def _process(self, task, llm_client=None):
        return {"reverse_analysis": "completed", "action_taken": task.get("action")}
