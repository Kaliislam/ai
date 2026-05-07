from turkish_jarvis.agents.base_agent import BaseAgent


class JarvisCEO(BaseAgent):
    """Patron ajan -- tüm council'lere emir verir."""

    def __init__(self):
        super().__init__("Jarvis", "CEO", "Executive", "llama3.1:70b")
        self.subordinates: list[str] = []

    async def _process(self, task, llm_client=None):
        return {"action": "delegated", "target": task.get("target_department")}

    async def delegate(self, task: dict, council_manager) -> dict:
        """Görevi dogru council'e dagit."""
        dept = task.get("department", "engineering")
        return await council_manager.execute_in_department(dept, task)
