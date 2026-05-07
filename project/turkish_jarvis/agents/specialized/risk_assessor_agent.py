"""RiskAssessor Agent — Risk değerlendirici."""

from turkish_jarvis.agents.base_agent import BaseAgent


class RiskAssessorAgent(BaseAgent):
    """Risk değerlendirici — risk matrisi, etki analizi, risk register."""

    def __init__(self):
        super().__init__("RiskAssessor", "Risk Assessor", "Specialized", "qwen3-coder:30b")
        self.skills = ["risk_matrix", "impact", "likelihood", "register"]

    async def _process(self, task, llm_client=None):
        return {"risk_report": "assessed", "action_taken": task.get("action")}
