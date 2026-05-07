from turkish_jarvis.agents.base_agent import BaseAgent


class QAEngineer(BaseAgent):
    """Test mühendisi -- otomasyon, manuel test ve kalite güvencesi."""

    def __init__(self):
        super().__init__("QAEng", "QA Engineer", "Engineering")
        self.skills = ["selenium", "pytest", "cypress", "load_testing", "test_planning"]

    async def _process(self, task, llm_client=None):
        return {"action": "test_execution", "suite": task.get("test_suite")}
