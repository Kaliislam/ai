from turkish_jarvis.agents.base_agent import BaseAgent


class BiologistAgent(BaseAgent):
    """Biyolog ajani — biyolojik veri ve sistem analizi."""
    def __init__(self):
        super().__init__("Biologist", "Biologist", "Research", "qwen3-coder:30b")
        self.skills = ["genomics", "ecology", "bioinformatics", "phenotype_analysis"]

    async def _process(self, task, llm_client=None):
        # Biyolojik analiz mantigi
        specimen = task.get('specimen', '')
        return {'analysis': 'done', 'specimen': specimen, 'classification': ''}
