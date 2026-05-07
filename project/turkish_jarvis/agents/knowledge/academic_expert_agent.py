from turkish_jarvis.agents.base_agent import BaseAgent


class AcademicExpertAgent(BaseAgent):
    """Akademik Uzman — academic_search, citations, papers, journals."""

    def __init__(self):
        super().__init__("academicexpert", "Akademik Uzman", "Knowledge", "gemma4:latest")
        self.skills = ["academic_search", "citations", "papers", "journals"]

    async def _process(self, task, llm_client=None):
        return {"agent": "academicexpert", "processed": task.get("count", 0)}
