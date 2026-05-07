from turkish_jarvis.agents.base_agent import BaseAgent


class ProjectManagerAgent(BaseAgent):
    """Proje yoneticisi ajani — gorev planlama ve takip."""
    def __init__(self):
        super().__init__("ProjectManager", "Project Manager", "Operations", "qwen3-coder:30b")
        self.skills = ["planning", "scheduling", "risk_analysis", "resource_allocation"]

    async def _process(self, task, llm_client=None):
        # Gorev planlama mantigi
        tasks = task.get('tasks', [])
        return {'plan': 'created', 'tasks': tasks, 'phases': len(tasks)}
