from turkish_jarvis.agents.base_agent import BaseAgent


class LegalAdvisorAgent(BaseAgent):
    """Hukuk danisman ajani — sozlesme ve hukuki degerlendirme."""
    def __init__(self):
        super().__init__("LegalAdvisor", "Legal Advisor", "Operations", "qwen3-coder:30b")
        self.skills = ["contract_review", "legal_analysis", "ip_protection", "dispute_advice"]

    async def _process(self, task, llm_client=None):
        # Hukuki degerlendirme mantigi
        document = task.get('document', '')
        return {'review': 'complete', 'document': document, 'clauses': []}
