"""Docker Agent — Docker uzmanı."""

from turkish_jarvis.agents.base_agent import BaseAgent


class DockerAgent(BaseAgent):
    """Docker uzmanı — container yönetimi, Dockerfile, Compose."""

    def __init__(self):
        super().__init__("Docker", "Docker Specialist", "Systems", "qwen3-coder:30b")
        self.skills = ["containers", "dockerfile", "compose", "registry"]

    async def _process(self, task, llm_client=None):
        return {"container_status": "running", "action_taken": task.get("action")}
