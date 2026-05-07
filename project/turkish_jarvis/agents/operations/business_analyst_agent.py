from turkish_jarvis.agents.base_agent import BaseAgent


class BusinessAnalystAgent(BaseAgent):
    """Is analisti ajani — gereksinim analizi ve surec tasarimi."""
    def __init__(self):
        super().__init__("BusinessAnalyst", "Business Analyst", "Operations", "qwen3-coder:30b")
        self.skills = ["requirements_analysis", "stakeholder_interviews", "process_modeling", "use_cases"]

    async def _process(self, task, llm_client=None):
        # Gereksinim analizi mantigi
        reqs = task.get('requirements', [])
        return {'analysis': 'complete', 'requirements': reqs, 'priority_map': {}}
