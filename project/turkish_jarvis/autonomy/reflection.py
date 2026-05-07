"""Düşünce ve öz-değerlendirme — Chain of Thought, self-evaluation, refinement."""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.reflection")


@dataclass
class CoTResult:
    """Chain-of-Thought sonucu."""

    steps: list[dict] = field(default_factory=list)
    final_answer: str = ""
    confidence: float = 0.0
    total_tokens: int = 0


@dataclass
class EvaluationResult:
    """Yanıt değerlendirmesi."""

    accuracy: float = 0.0
    completeness: float = 0.0
    source_quality: float = 0.0
    language_quality: float = 0.0
    overall_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class HallucinationCheck:
    """Hallucination kontrolü sonucu."""

    has_hallucination: bool = False
    confidence: float = 0.0
    unsupported_claims: list[str] = field(default_factory=list)
    verified_claims: list[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class ReflectionResult:
    """Tam pipeline sonucu."""

    final_response: str = ""
    initial_response: str = ""
    refinement_count: int = 0
    final_evaluation: EvaluationResult = field(default_factory=EvaluationResult)
    reasoning_summary: str = ""
    hallucination_safe: bool = True
    metadata: dict = field(default_factory=dict)


class ReflectionEngine:
    """LLM çıktılarını eleştirip iyileştiren motor."""

    def __init__(self, llm_client):
        self.llm = llm_client

    # ------------------------------------------------------------------
    # 1. Chain-of-Thought
    # ------------------------------------------------------------------
    async def chain_of_thought(
        self,
        question: str,
        context: dict,
        max_steps: int = 5,
    ) -> CoTResult:
        """Adım adım düşünerek yanıt üret."""
        steps: list[dict] = []
        accumulated_knowledge = ""
        total_tokens = 0

        for step_num in range(1, max_steps + 1):
            prompt = self._build_cot_step_prompt(
                question=question,
                context=context,
                step_num=step_num,
                accumulated=accumulated_knowledge,
            )
            raw = await self._call_llm(prompt)
            total_tokens += self._estimate_tokens(raw)

            parsed = self._parse_cot_step(raw, step_num)
            steps.append(parsed)
            accumulated_knowledge += f"\n[Adım {step_num}] {parsed.get('result', '')}"

            if parsed.get("done", False):
                break

        final_prompt = self._build_final_answer_prompt(
            question=question, steps=steps, context=context
        )
        final_raw = await self._call_llm(final_prompt)
        total_tokens += self._estimate_tokens(final_raw)

        confidence = self._extract_confidence(final_raw)
        final_answer = self._extract_answer(final_raw)

        return CoTResult(
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            total_tokens=total_tokens,
        )

    def _build_cot_step_prompt(
        self,
        question: str,
        context: dict,
        step_num: int,
        accumulated: str,
    ) -> str:
        return (
            f"Soru: {question}\n"
            f"Bağlam: {json.dumps(context, ensure_ascii=False, default=str)}\n"
            f"Şu ana kadar biriken bilgi: {accumulated}\n"
            f"Adım {step_num}:\n"
            "1. Şu ana kadar ne biliyorum?\n"
            "2. Sıradaki en iyi eylem nedir?\n"
            "3. Bu adımın sonucu ne?\n"
            "Yanıtı JSON formatında ver: "
            '{"thought": "...", "action": "...", "result": "...", "done": true/false}'
        )

    def _build_final_answer_prompt(
        self, question: str, steps: list[dict], context: dict
    ) -> str:
        steps_text = "\n".join(
            f"Adım {s['step']}: {s.get('thought', '')} → {s.get('result', '')}"
            for s in steps
        )
        return (
            f"Soru: {question}\n"
            f"Düşünce adımları:\n{steps_text}\n"
            f"Bağlam: {json.dumps(context, ensure_ascii=False, default=str)}\n"
            "Yukarıdaki adımları birleştirerek nihai yanıtı üret.\n"
            "Yanıtın sonuna güven skoru ekle: [Güven: X.XX]"
        )

    def _parse_cot_step(self, raw: str, step_num: int) -> dict:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"thought": raw, "action": "", "result": raw, "done": False}
        data["step"] = step_num
        return data

    # ------------------------------------------------------------------
    # 2. Self-Evaluation
    # ------------------------------------------------------------------
    async def self_evaluate(
        self,
        response: str,
        original_question: str,
        context: dict,
    ) -> EvaluationResult:
        """Üretilen yanıtı değerlendir."""
        prompt = (
            f"Orijinal soru: {original_question}\n"
            f"Üretilen yanıt: {response}\n"
            f"Bağlam: {json.dumps(context, ensure_ascii=False, default=str)}\n"
            "Yanıtı aşağıdaki kriterlere göre 0-1 arası skorla:\n"
            "- Doğruluk (accuracy)\n"
            "- Eksiksizlik (completeness)\n"
            "- Kaynak kalitesi (source_quality)\n"
            "- Dil kalitesi (language_quality)\n"
            "Sorunları ve iyileştirme önerilerini de listele.\n"
            "JSON format: "
            '{"accuracy": 0.XX, "completeness": 0.XX, "source_quality": 0.XX, '
            '"language_quality": 0.XX, "overall_score": 0.XX, '
            '"issues": ["..."], "suggestions": ["..."]}'
        )
        raw = await self._call_llm(prompt)
        return self._parse_evaluation(raw)

    def _parse_evaluation(self, raw: str) -> EvaluationResult:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Değerlendirme JSON parse hatası, varsayılan değerler.")
            return EvaluationResult(
                issues=["JSON parse hatası"],
                suggestions=["Ham metin değerlendirmesi yapıldı."],
            )
        return EvaluationResult(
            accuracy=float(data.get("accuracy", 0.0)),
            completeness=float(data.get("completeness", 0.0)),
            source_quality=float(data.get("source_quality", 0.0)),
            language_quality=float(data.get("language_quality", 0.0)),
            overall_score=float(data.get("overall_score", 0.0)),
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
        )

    # ------------------------------------------------------------------
    # 3. Refinement
    # ------------------------------------------------------------------
    async def refine(
        self,
        response: str,
        evaluation: EvaluationResult,
        original_question: str,
    ) -> str:
        """Değerlendirmeye göre yanıtı iyileştir."""
        issues_text = "\n".join(f"- {i}" for i in evaluation.issues)
        suggestions_text = "\n".join(f"- {s}" for s in evaluation.suggestions)
        prompt = (
            f"Orijinal soru: {original_question}\n"
            f"Mevcut yanıt: {response}\n"
            f"Sorunlar:\n{issues_text}\n"
            f"Öneriler:\n{suggestions_text}\n"
            "Yukarıdaki sorunları gidererek iyileştirilmiş yanıtı üret.\n"
            "Eksik bilgi varsa belirt, kaynak belirtemiyorsan 'emin değilim' de."
        )
        return await self._call_llm(prompt)

    # ------------------------------------------------------------------
    # 4. Full Pipeline: reflect_and_answer
    # ------------------------------------------------------------------
    async def reflect_and_answer(
        self,
        question: str,
        context: dict,
        required_quality: float = 0.85,
    ) -> ReflectionResult:
        """Tam pipeline: CoT → üret → değerlendir → iyileştir → döndür."""
        max_refinements = 3
        refinement_count = 0

        # 1. Chain-of-Thought
        cot = await self.chain_of_thought(question, context)
        initial_response = cot.final_answer
        current_response = initial_response

        # 2. İlk değerlendirme
        evaluation = await self.self_evaluate(
            current_response, question, context
        )

        # 3. İyileştirme döngüsü
        while evaluation.overall_score < required_quality and refinement_count < max_refinements:
            logger.info(
                "Yanıt kalitesi düşük (%.2f < %.2f), iyileştirme #%d yapılıyor...",
                evaluation.overall_score,
                required_quality,
                refinement_count + 1,
            )
            current_response = await self.refine(
                current_response, evaluation, question
            )
            evaluation = await self.self_evaluate(
                current_response, question, context
            )
            refinement_count += 1

        # 4. Hallucination kontrolü (RAG kaynakları varsa)
        rag_sources = context.get("rag_sources", [])
        hallucination = await self.detect_hallucination(current_response, rag_sources)
        if hallucination.has_hallucination:
            current_response = (
                f"{current_response}\n\n[Uyarı: Aşağıdaki iddialar kaynaklarımızla "
                f"doğrulanamadı: {', '.join(hallucination.unsupported_claims)}]"
            )

        # 5. Düşünce özeti
        reasoning_summary = await self.summarize_reasoning(cot)

        return ReflectionResult(
            final_response=current_response,
            initial_response=initial_response,
            refinement_count=refinement_count,
            final_evaluation=evaluation,
            reasoning_summary=reasoning_summary,
            hallucination_safe=not hallucination.has_hallucination,
            metadata={
                "cot_steps": len(cot.steps),
                "total_tokens": cot.total_tokens,
                "required_quality": required_quality,
                "hallucination_confidence": hallucination.confidence,
            },
        )

    # ------------------------------------------------------------------
    # 5. Summarize reasoning
    # ------------------------------------------------------------------
    async def summarize_reasoning(
        self,
        cot_result: CoTResult,
        max_length: int = 200,
    ) -> str:
        """Uzun düşünce zincirini özetle."""
        steps_text = "\n".join(
            f"Adım {s['step']}: {s.get('thought', '')}"
            for s in cot_result.steps
        )
        prompt = (
            f"Aşağıdaki {len(cot_result.steps)} adımlık düşünce zincirini "
            f"en fazla {max_length} karakter ve 2 cümlede özetle:\n"
            f"{steps_text}"
        )
        summary = await self._call_llm(prompt)
        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."
        return summary

    # ------------------------------------------------------------------
    # 6. Hallucination detection
    # ------------------------------------------------------------------
    async def detect_hallucination(
        self,
        response: str,
        rag_sources: list[dict],
    ) -> HallucinationCheck:
        """Yanıtta uydurma bilgi var mı kontrol et."""
        if not rag_sources:
            logger.debug("RAG kaynağı yok; hallucination kontrolü atlanıyor.")
            return HallucinationCheck(
                has_hallucination=False,
                recommendation="RAG kaynağı olmadan kontrol yapılamadı.",
            )

        sources_text = "\n".join(
            f"[{i + 1}] {src.get('content', src.get('text', ''))}"
            for i, src in enumerate(rag_sources[:5])  # ilk 5 kaynak
        )
        prompt = (
            f"Yanıt: {response}\n"
            f"RAG Kaynakları:\n{sources_text}\n"
            "Yanıttaki her iddiayı kaynaklarla karşılaştır.\n"
            "JSON format: "
            '{"has_hallucination": true/false, "confidence": 0.XX, '
            '"unsupported_claims": ["..."], "verified_claims": ["..."], '
            '"recommendation": "..."}'
        )
        raw = await self._call_llm(prompt)
        return self._parse_hallucination(raw)

    def _parse_hallucination(self, raw: str) -> HallucinationCheck:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Hallucination JSON parse hatası.")
            return HallucinationCheck(
                has_hallucination=False,
                recommendation="Parse hatası; manuel kontrol önerilir.",
            )
        return HallucinationCheck(
            has_hallucination=bool(data.get("has_hallucination", False)),
            confidence=float(data.get("confidence", 0.0)),
            unsupported_claims=data.get("unsupported_claims", []),
            verified_claims=data.get("verified_claims", []),
            recommendation=data.get("recommendation", ""),
        )

    # ------------------------------------------------------------------
    # Yardımcı metodlar
    # ------------------------------------------------------------------
    async def _call_llm(self, prompt: str) -> str:
        """LLM istemcisi üzerinden çağrı yap."""
        if self.llm is None:
            raise RuntimeError("LLM istemcisi atanmamış.")
        return await self.llm.generate(prompt)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Basit token tahmini (Türkçe için ~1.5 karakter/token)."""
        return max(1, int(len(text) / 1.5))

    @staticmethod
    def _extract_confidence(text: str) -> float:
        """Metinden [Güven: X.XX] formatında skor çıkar."""
        import re
        match = re.search(r"Güven:\s*([0-9.]+)", text)
        if match:
            try:
                return min(1.0, max(0.0, float(match.group(1))))
            except ValueError:
                pass
        return 0.5

    @staticmethod
    def _extract_answer(text: str) -> str:
        """Metinden [Güven: ...] etiketini temizle."""
        import re
        return re.sub(r"\s*\[Güven:\s*[0-9.]+\]\s*", "", text).strip()
