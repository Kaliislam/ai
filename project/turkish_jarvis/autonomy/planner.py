"""Çok adımlı planlama motoru — ReAct + HTN pattern.

Bu modül, kullanıcı taleplerini analiz eder, alt-görevlere ayırır,
adım adım yürütür, hata durumunda yeniden planlar ve meta-öğrenme
verileri üretir. ReAct (Reasoning + Acting) pattern'ini takip eder.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, TypeAlias

from turkish_jarvis.memory.graph import GraphMemory
from turkish_jarvis.tools.registry import ToolRegistry

logger = logging.getLogger("jarvis.planner")

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

StepStatus: TypeAlias = str  # "pending" | "running" | "success" | "failed" | "skipped"
ActionType: TypeAlias = str  # "tool" | "llm_reason" | "sub_objective"


# ---------------------------------------------------------------------------
# Protocol: LLM Client (loosely coupled)
# ---------------------------------------------------------------------------

class LLMClientProtocol(Protocol):
    """Abstract interface for the LLM client used by the planner."""

    async def chat(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        """Send a prompt to the LLM and return the response text."""
        ...


# ---------------------------------------------------------------------------
# Protocol: Meta Learning
# ---------------------------------------------------------------------------

class MetaLearningProtocol(Protocol):
    """Abstract interface for meta-learning feedback collection."""

    async def report_performance(
        self,
        objective: str,
        plan_steps: int,
        success: bool,
        replan_count: int,
        execution_time: float,
        lessons: list[str],
    ) -> None:
        """Store a performance report for future plan optimization."""
        ...


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class PlanStep:
    """A single step inside an execution plan."""

    step_id: str
    action_type: ActionType  # "tool" | "llm_reason" | "sub_objective"
    action: str  # tool name or prompt / sub-objective text
    args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    expected_output: str = ""
    status: StepStatus = "pending"
    result: Any = None
    error: str | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize step to a JSON-compatible dict."""
        return {
            "step_id": self.step_id,
            "action_type": self.action_type,
            "action": self.action,
            "args": self.args,
            "depends_on": self.depends_on,
            "expected_output": self.expected_output,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanStep:
        """Reconstruct a PlanStep from a dict."""
        return cls(
            step_id=data["step_id"],
            action_type=data["action_type"],
            action=data["action"],
            args=data.get("args", {}),
            depends_on=data.get("depends_on", []),
            expected_output=data.get("expected_output", ""),
            status=data.get("status", "pending"),
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class Plan:
    """An executable plan produced by the planner."""

    steps: list[PlanStep]
    objective: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    estimated_steps: int = 0
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict[str, Any]:
        """Serialize plan to a JSON-compatible dict."""
        return {
            "plan_id": self.plan_id,
            "objective": self.objective,
            "created_at": self.created_at.isoformat(),
            "estimated_steps": self.estimated_steps,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        """Reconstruct a Plan from a dict."""
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow()
        return cls(
            steps=[PlanStep.from_dict(s) for s in data.get("steps", [])],
            objective=data["objective"],
            created_at=created_at,
            estimated_steps=data.get("estimated_steps", 0),
            plan_id=data.get("plan_id", str(uuid.uuid4())[:8]),
        )

    def is_complete(self) -> bool:
        """Return True if all steps are done (success, failed, or skipped)."""
        return all(s.status in ("success", "failed", "skipped") for s in self.steps)

    def pending_steps(self) -> list[PlanStep]:
        """Return steps whose dependencies are satisfied but not yet run."""
        completed_ids = {s.step_id for s in self.steps if s.status == "success"}
        return [
            s for s in self.steps
            if s.status == "pending"
            and all(d in completed_ids for d in s.depends_on)
        ]

    def failed_steps(self) -> list[PlanStep]:
        """Return steps that failed."""
        return [s for s in self.steps if s.status == "failed"]


@dataclass
class ExecutionResult:
    """Result of executing a plan."""

    success: bool
    final_output: str
    step_results: list[dict[str, Any]] = field(default_factory=list)
    replan_count: int = 0
    execution_time: float = 0.0
    lessons_learned: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to a JSON-compatible dict."""
        return {
            "success": self.success,
            "final_output": self.final_output,
            "step_results": self.step_results,
            "replan_count": self.replan_count,
            "execution_time": self.execution_time,
            "lessons_learned": self.lessons_learned,
        }


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------


class TaskPlanner:
    """Kullanıcı talebini alt-görevlere ayırır ve yürütür.

    - plan: LLM'e "bu görevi nasıl yaparım?" diye sorar, JSON adım listesi üretir.
    - execute_plan: Adımları bağımlılıklara göre sırayla veya paralel olarak çalıştırır.
    - replan: Başarısız adım için alternatif strateji üretir.

    Entegrasyon:
    - ToolRegistry'den araç şemaları alır.
    - LLMClient'tan reasoning yapar.
    - GraphMemory'e plan sonuçlarını kaydeder.
    - MetaLearning'e performans raporu gönderir.
    """

    def __init__(
        self,
        llm_client: LLMClientProtocol | None = None,
        meta_learning: MetaLearningProtocol | None = None,
        graph_memory: GraphMemory | None = None,
        max_replan: int = 5,
    ) -> None:
        self.llm_client = llm_client
        self.meta_learning = meta_learning
        self.graph_memory = graph_memory
        self.max_replan = max_replan

    # -------------------------------------------------------------------
    # Planning
    # -------------------------------------------------------------------

    async def plan(
        self,
        objective: str,
        context: dict[str, Any],
        tool_registry: ToolRegistry | None = None,
    ) -> Plan:
        """LLM'e sorarak görevi adımlara böl, Plan üret.

        Args:
            objective: Kullanıcının isteği (doğal dil).
            context: Oturum bağlamı (önceki mesajlar, kullanıcı profili, vb.).
            tool_registry: Mevcut araçlar ve şemaları (planlama prompt'una dahil edilir).

        Returns:
            Plan: Adımları, bağımlılıkları ve beklentileri içeren plan.
        """
        schemas: list[dict[str, Any]] = []
        if tool_registry is not None:
            schemas = tool_registry.get_schemas()

        system_prompt = self._build_planning_system_prompt(schemas)
        user_prompt = self._build_planning_user_prompt(objective, context)

        if self.llm_client is None:
            logger.warning("LLM client yok; default single-step plan üretiliyor.")
            return self._fallback_plan(objective)

        raw_response = await self.llm_client.chat(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.2,
        )

        plan = self._parse_plan_from_response(objective, raw_response)
        plan.estimated_steps = len(plan.steps)
        logger.info(
            "Plan üretildi: %d adım | plan_id=%s", len(plan.steps), plan.plan_id
        )
        return plan

    # -------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------

    async def execute_plan(
        self,
        plan: Plan,
        tool_registry: ToolRegistry | None = None,
        llm_client: LLMClientProtocol | None = None,
    ) -> ExecutionResult:
        """Planı adım adım yürüt; hata olursa replan yap.

        Args:
            plan: Çalıştırılacak Plan nesnesi.
            tool_registry: Araç çağrıları için registry.
            llm_client: Reasoning adımları için LLM istemcisi.

        Returns:
            ExecutionResult: Başarı durumu, toplam çıktı, öğrenilen dersler.
        """
        llm = llm_client or self.llm_client
        start_time = datetime.utcnow().timestamp()
        replan_count = 0
        lessons: list[str] = []
        step_results: list[dict[str, Any]] = []

        while not plan.is_complete():
            pending = plan.pending_steps()
            if not pending:
                # Tüm adımlar bağımlı ama hiçbiri çalışmadı → deadlock
                failed = plan.failed_steps()
                if failed and replan_count < self.max_replan:
                    for fs in failed:
                        remaining = [s for s in plan.steps if s.status in ("pending", "running")]
                        new_plan = await self.replan(
                            failed_step=fs,
                            error=fs.error or "unknown error",
                            remaining_steps=remaining,
                            tool_registry=tool_registry,
                        )
                        plan.steps.extend(new_plan.steps)
                        replan_count += 1
                        lessons.append(
                            f"Replan #{replan_count}: '{fs.step_id}' için alternatif strateji eklendi."
                        )
                        fs.status = "skipped"  # eski adım atlandı
                        break
                else:
                    break  # deadlock, çık

            # Bağımsız adımları paralel çalıştır
            tasks = [self._execute_step(s, plan, tool_registry, llm) for s in pending]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Her iterasyonda sonuçları topla
            for step in plan.steps:
                if step.status in ("success", "failed"):
                    step_results.append(step.to_dict())

        # Sonuçları derle
        execution_time = datetime.utcnow().timestamp() - start_time
        success = all(s.status == "success" for s in plan.steps)
        final_output = self._compile_final_output(plan)

        result = ExecutionResult(
            success=success,
            final_output=final_output,
            step_results=step_results,
            replan_count=replan_count,
            execution_time=execution_time,
            lessons_learned=lessons,
        )

        # GraphMemory'e kaydet
        await self._save_to_graph_memory(plan, result)

        # MetaLearning'e rapor gönder
        await self._send_meta_learning_report(plan, result)

        logger.info(
            "Plan tamamlandı | success=%s | replan=%d | time=%.2fs",
            success,
            replan_count,
            execution_time,
        )
        return result

    # -------------------------------------------------------------------
    # Replanning
    # -------------------------------------------------------------------

    async def replan(
        self,
        failed_step: PlanStep,
        error: str,
        remaining_steps: list[PlanStep],
        tool_registry: ToolRegistry | None = None,
    ) -> Plan:
        """Başarısız adım için alternatif strateji üret.

        Args:
            failed_step: Hata veren adım.
            error: Hata mesajı.
            remaining_steps: Çalıştırılmayı bekleyen adımlar.
            tool_registry: Araç şemaları.

        Returns:
            Plan: Yeni alternatif adımları içeren plan (eski plana eklenecek).
        """
        schemas: list[dict[str, Any]] = []
        if tool_registry is not None:
            schemas = tool_registry.get_schemas()

        system_prompt = self._build_replan_system_prompt(schemas)
        user_prompt = (
            f"Başarısız adım: {failed_step.step_id}\n"
            f"Aksiyon: {failed_step.action}\n"
            f"Hata: {error}\n"
            f"Beklenen çıktı: {failed_step.expected_output}\n"
            f"Kalan adımlar: {[s.step_id for s in remaining_steps]}\n"
            "Lütfen bu adım için alternatif bir strateji öner."
        )

        if self.llm_client is None:
            logger.warning("LLM client yok; replan yapılamıyor, boş plan döndürülüyor.")
            return Plan(steps=[], objective="replan_fallback")

        raw_response = await self.llm_client.chat(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
        )

        # Replan response'ını normal plan gibi parse et
        plan = self._parse_plan_from_response(f"replan_for_{failed_step.step_id}", raw_response)
        # Bağımlılıkları eski adıma bağla
        for step in plan.steps:
            if not step.depends_on:
                step.depends_on = [failed_step.step_id]
        logger.info("Replan üretildi: %d yeni adım", len(plan.steps))
        return plan

    # -------------------------------------------------------------------
    # Step Execution
    # -------------------------------------------------------------------

    async def _execute_step(
        self,
        step: PlanStep,
        plan: Plan,
        tool_registry: ToolRegistry | None,
        llm_client: LLMClientProtocol | None,
    ) -> None:
        """Tek bir plan adımını çalıştır."""
        step.status = "running"
        logger.debug("Adım çalışıyor: %s (%s)", step.step_id, step.action_type)

        try:
            if step.action_type == "tool":
                if tool_registry is None:
                    raise RuntimeError("Tool adımı çalıştırılacak ama ToolRegistry yok.")
                result = await tool_registry.execute(step.action, step.args)
                step.result = result
                step.status = "success"

            elif step.action_type == "llm_reason":
                if llm_client is None:
                    raise RuntimeError("LLM reasoning adımı çalıştırılacak ama LLMClient yok.")
                # Değişken interpolasyonu: önceki adımların sonuçlarını prompt'a inject et
                prompt = self._interpolate_step_args(step.action, plan)
                result = await llm_client.chat(prompt=prompt, temperature=0.4)
                step.result = result
                step.status = "success"

            elif step.action_type == "sub_objective":
                # Alt hedef: kendi içinde recursive planlama
                sub_plan = await self.plan(
                    objective=step.action,
                    context={"parent_plan_id": plan.plan_id, "step_id": step.step_id},
                    tool_registry=tool_registry,
                )
                sub_result = await self.execute_plan(
                    plan=sub_plan,
                    tool_registry=tool_registry,
                    llm_client=llm_client,
                )
                step.result = sub_result.to_dict()
                step.status = "success" if sub_result.success else "failed"
                if not sub_result.success:
                    step.error = f"Sub-objective failed: {sub_result.final_output}"

            else:
                raise ValueError(f"Bilinmeyen action_type: {step.action_type}")

        except Exception as exc:
            step.status = "failed"
            step.error = f"{type(exc).__name__}: {exc}"
            step.retry_count += 1
            logger.warning(
                "Adım başarısız: %s | hata=%s | retry=%d",
                step.step_id,
                step.error,
                step.retry_count,
            )

    # -------------------------------------------------------------------
    # Prompt Builders
    # -------------------------------------------------------------------

    def _build_planning_system_prompt(
        self, tool_schemas: list[dict[str, Any]]
    ) -> str:
        """Planlama için sistem prompt'u oluştur."""
        tools_text = json.dumps(tool_schemas, ensure_ascii=False, indent=2)
        return (
            "Sen bir görev planlama asistanısın. Kullanıcının talebini analiz edip "
            "JSON formatında bir adım listesi üretmelisin.\n\n"
            "Kurallar:\n"
            "1. Her adım bir 'step_id', 'action_type', 'action', 'args' içermeli.\n"
            "2. action_type: 'tool', 'llm_reason', veya 'sub_objective' olabilir.\n"
            "3. 'tool' kullanıyorsan mevcut araçlardan birini seç.\n"
            "4. 'depends_on' dizisiyle bağımlılıkları belirt.\n"
            "5. 'expected_output' ile ne beklediğini açıkla.\n"
            "6. Sadece JSON döndür; başka metin ekleme.\n\n"
            f"Mevcut araçlar:\n{tools_text}\n\n"
            "JSON formatı:\n"
            '{\n'
            '  "steps": [\n'
            '    {\n'
            '      "step_id": "step_1",\n'
            '      "action_type": "tool",\n'
            '      "action": "web_search",\n'
            '      "args": {"query": "..."},\n'
            '      "depends_on": [],\n'
            '      "expected_output": "..."\n'
            '    }\n'
            '  ]\n'
            '}\n'
        )

    def _build_planning_user_prompt(
        self, objective: str, context: dict[str, Any]
    ) -> str:
        """Planlama için kullanıcı prompt'u oluştur."""
        ctx = json.dumps(context, ensure_ascii=False, default=str)
        return (
            f"Kullanıcı talebi: {objective}\n"
            f"Bağlam: {ctx}\n\n"
            "Lütfen bu görevi yerine getirmek için adım adım bir plan üret."
        )

    def _build_replan_system_prompt(
        self, tool_schemas: list[dict[str, Any]]
    ) -> str:
        """Replanning için sistem prompt'u oluştur."""
        tools_text = json.dumps(tool_schemas, ensure_ascii=False, indent=2)
        return (
            "Sen bir hata kurtarma planlayıcısısın. Başarısız olan bir adım için "
            "alternatif strateji üretmelisin.\n\n"
            "Kurallar:\n"
            "1. Sorunun kaynağını analiz et (eksik bilgi, araç hatası, vb.).\n"
            "2. Farklı bir araç veya farklı parametrelerle alternatif adımlar öner.\n"
            "3. JSON formatında adım listesi döndür.\n\n"
            f"Mevcut araçlar:\n{tools_text}\n\n"
            "JSON formatı: planning prompt ile aynı."
        )

    # -------------------------------------------------------------------
    # Parsing
    # -------------------------------------------------------------------

    def _parse_plan_from_response(self, objective: str, raw_response: str) -> Plan:
        """LLM yanıtını parse ederek Plan nesnesi üret."""
        # JSON bloğunu çıkar (markdown code block veya düz JSON)
        text = raw_response.strip()
        if text.startswith("```"):
            # ```json ... ``` bloğunu çıkar
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # LLM düzgün JSON vermediyse, metni line-by-line parse etmeyi dene
            logger.warning("LLM yanıtı düzgün JSON değil, heuristic parse deneniyor.")
            data = self._heuristic_parse(text)

        steps_data = data.get("steps", [])
        if not steps_data and isinstance(data, list):
            steps_data = data  # düz liste de kabul et

        steps: list[PlanStep] = []
        for i, sd in enumerate(steps_data):
            step_id = sd.get("step_id", f"step_{i + 1}")
            steps.append(
                PlanStep(
                    step_id=step_id,
                    action_type=sd.get("action_type", "llm_reason"),
                    action=sd.get("action", sd.get("prompt", "")),
                    args=sd.get("args", {}),
                    depends_on=sd.get("depends_on", []),
                    expected_output=sd.get("expected_output", ""),
                )
            )
        return Plan(steps=steps, objective=objective)

    def _heuristic_parse(self, text: str) -> dict[str, Any]:
        """LLM JSON döndürmemişse, basit heuristic ile adım listesi çıkar."""
        steps: list[dict[str, Any]] = []
        lines = text.splitlines()
        current: dict[str, Any] = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("adım") or line.lower().startswith("step"):
                if current:
                    steps.append(current)
                current = {"step_id": f"step_{len(steps) + 1}", "action_type": "llm_reason"}
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower()
                val = val.strip()
                if key in ("action", "aksiyon", "işlem"):
                    current["action"] = val
                elif key in ("tool", "araç"):
                    current["action_type"] = "tool"
                    current["action"] = val
                elif key in ("args", "argümanlar", "parametreler"):
                    try:
                        current["args"] = json.loads(val)
                    except Exception:
                        current["args"] = {"query": val}
                elif key in ("beklenen", "expected"):
                    current["expected_output"] = val
        if current:
            steps.append(current)
        if not steps:
            # Hiçbir şey bulunamazsa, tüm metni tek bir reasoning adımı olarak kabul et
            steps = [
                {
                    "step_id": "step_1",
                    "action_type": "llm_reason",
                    "action": text,
                    "args": {},
                    "expected_output": "Kullanıcı talebine doğrudan yanıt.",
                }
            ]
        return {"steps": steps}

    # -------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------

    def _fallback_plan(self, objective: str) -> Plan:
        """LLM client yoksa tek adımlı fallback plan üret."""
        return Plan(
            steps=[
                PlanStep(
                    step_id="step_1",
                    action_type="llm_reason",
                    action=objective,
                    expected_output="Doğrudan yanıt.",
                )
            ],
            objective=objective,
        )

    def _interpolate_step_args(self, template: str, plan: Plan) -> str:
        """Prompt şablonunda {{step_id.result}} yer tutucularını çözümle."""
        result = template
        for step in plan.steps:
            if step.status == "success" and step.result is not None:
                placeholder = f"{{{{{step.step_id}.result}}}}"
                result_str = str(step.result)
                result = result.replace(placeholder, result_str)
        return result

    def _compile_final_output(self, plan: Plan) -> str:
        """Tüm başarılı adımların sonuçlarını birleştirerek özet çıktı üret."""
        outputs: list[str] = []
        for step in plan.steps:
            if step.status == "success" and step.result is not None:
                outputs.append(f"[{step.step_id}] {step.result}")
        if not outputs:
            failed = [s for s in plan.steps if s.status == "failed"]
            if failed:
                return f"Plan başarısız. Hatalar: {[s.error for s in failed]}"
            return "Plan tamamlandı ancak çıktı üretilmedi."
        return "\n".join(outputs)

    async def _save_to_graph_memory(self, plan: Plan, result: ExecutionResult) -> None:
        """Plan sonuçlarını GraphMemory'e kaydet."""
        if self.graph_memory is None:
            return
        try:
            plan_entity = f"plan_{plan.plan_id}"
            self.graph_memory.add_entity(
                name=plan_entity,
                type="plan",
                attributes={
                    "objective": plan.objective,
                    "success": result.success,
                    "replan_count": result.replan_count,
                    "execution_time": result.execution_time,
                    "steps": [s.step_id for s in plan.steps],
                },
            )
            # Plan adımlarını da bağla
            for step in plan.steps:
                step_entity = f"step_{step.step_id}"
                self.graph_memory.add_entity(
                    name=step_entity,
                    type="plan_step",
                    attributes={
                        "action_type": step.action_type,
                        "action": step.action,
                        "status": step.status,
                        "result_preview": str(step.result)[:200] if step.result else None,
                    },
                )
                self.graph_memory.add_relation(
                    from_entity=plan_entity,
                    to_entity=step_entity,
                    relation_type="contains",
                    context={"order": plan.steps.index(step)},
                )
            logger.debug("GraphMemory'e plan kaydedildi: %s", plan_entity)
        except Exception as exc:
            logger.warning("GraphMemory kaydı başarısız: %s", exc)

    async def _send_meta_learning_report(
        self, plan: Plan, result: ExecutionResult
    ) -> None:
        """Performans raporunu MetaLearning modülüne gönder."""
        if self.meta_learning is None:
            return
        try:
            await self.meta_learning.report_performance(
                objective=plan.objective,
                plan_steps=len(plan.steps),
                success=result.success,
                replan_count=result.replan_count,
                execution_time=result.execution_time,
                lessons=result.lessons_learned,
            )
            logger.debug("MetaLearning raporu gönderildi.")
        except Exception as exc:
            logger.warning("MetaLearning raporu gönderilemedi: %s", exc)

    # -------------------------------------------------------------------
    # Convenience API
    # -------------------------------------------------------------------

    async def run(
        self,
        objective: str,
        context: dict[str, Any],
        tool_registry: ToolRegistry | None = None,
        llm_client: LLMClientProtocol | None = None,
    ) -> ExecutionResult:
        """Tek çağrıda planla + çalıştır.

        Args:
            objective: Kullanıcının talebi.
            context: Oturum bağlamı.
            tool_registry: Araçlar.
            llm_client: LLM istemcisi (opsiyonel, init'deki kullanılır).

        Returns:
            ExecutionResult: Tam sonuç.
        """
        plan = await self.plan(
            objective=objective,
            context=context,
            tool_registry=tool_registry,
        )
        return await self.execute_plan(
            plan=plan,
            tool_registry=tool_registry,
            llm_client=llm_client or self.llm_client,
        )
