from turkish_jarvis.agents.base_agent import BaseAgent


class ScrumMasterAgent(BaseAgent):
    """Scrum master ajani — sprint yonetimi ve engel kaldirma."""
    def __init__(self):
        super().__init__("ScrumMaster", "Scrum Master", "Operations", "qwen3-coder:30b")
        self.skills = ["sprint_planning", "retrospectives", "daily_standups", "velocity_tracking"]

    async def _process(self, task, llm_client=None):
        # Sprint yonetimi mantigi
        sprints = task.get('sprints', [])
        return {'sprint': 'managed', 'sprints': sprints, 'blockers_resolved': 0}
