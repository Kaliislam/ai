from turkish_jarvis.agents.base_agent import BaseAgent


class HistorianAgent(BaseAgent):
    """Tarihci ajani — tarihsel arastirma ve kaynak analizi."""
    def __init__(self):
        super().__init__("Historian", "Historian", "Research", "qwen3-coder:30b")
        self.skills = ["archival_research", "chronology", "source_critique", "historiography"]

    async def _process(self, task, llm_client=None):
        # Tarihsel arastirma mantigi
        era = task.get('era', '')
        return {'research': 'done', 'era': era, 'events': []}
