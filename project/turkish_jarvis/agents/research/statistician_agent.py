from turkish_jarvis.agents.base_agent import BaseAgent


class StatisticianAgent(BaseAgent):
    """Istatistikci ajani — istatistiksel analiz ve hipotez testi."""
    def __init__(self):
        super().__init__("Statistician", "Statistician", "Research", "qwen3-coder:30b")
        self.skills = ["hypothesis_testing", "regression", "sampling", "significance_analysis"]

    async def _process(self, task, llm_client=None):
        # Istatistiksel analiz mantigi
        data = task.get('data', [])
        return {'test': 'run', 'p_value': None, 'data_points': len(data)}
