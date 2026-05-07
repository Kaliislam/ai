from turkish_jarvis.agents.base_agent import BaseAgent


class ConsultantAgent(BaseAgent):
    """Danisman ajani — stratejik tavsiye ve analiz."""
    def __init__(self):
        super().__init__("Consultant", "Consultant", "Operations", "qwen3-coder:30b")
        self.skills = ["strategy", "market_analysis", "business_modeling", "recommendations"]

    async def _process(self, task, llm_client=None):
        # Danismanlik mantigi
        problem = task.get('problem', '')
        return {'advice': 'provided', 'problem': problem, 'options': []}
