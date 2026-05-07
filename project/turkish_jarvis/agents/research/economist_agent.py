from turkish_jarvis.agents.base_agent import BaseAgent


class EconomistAgent(BaseAgent):
    """Ekonomist ajani — ekonomik analiz ve tahmin."""
    def __init__(self):
        super().__init__("Economist", "Economist", "Research", "qwen3-coder:30b")
        self.skills = ["macro_analysis", "forecasting", "market_modeling", "policy_impact"]

    async def _process(self, task, llm_client=None):
        # Ekonomik analiz mantigi
        indicator = task.get('indicator', '')
        return {'forecast': 'generated', 'indicator': indicator, 'trend': ''}
