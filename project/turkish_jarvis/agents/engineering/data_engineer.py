from turkish_jarvis.agents.base_agent import BaseAgent


class DataEngineer(BaseAgent):
    """Veri mühendisi -- ETL, veri gölleri ve akis işleme."""

    def __init__(self):
        super().__init__("DataEng", "Data Engineer", "Engineering")
        self.skills = ["spark", "kafka", "airflow", "dbt", "data_warehousing"]

    async def _process(self, task, llm_client=None):
        return {"action": "etl_pipeline", "source": task.get("data_source")}
