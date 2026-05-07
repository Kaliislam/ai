"""Ruflo SPARC Plugin Bridge.

SPARC = Specification, Pseudocode, Architecture, Refinement, Completion.
Yazılım geliştirme sürecini 5 fazda modelleyen bir asistan katmanı.
Her faz, önceki fazın çıktısını girdi olarak alır.

Bu modül pipeline koordinasyonu sağlar; gerçek kod üretimi
dış bir LLM / agent'a devredilir.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SparcPhase:
    """Bir SPARC fazının çıktısı."""

    name: str  # spec / pseudocode / architecture / refinement / completion
    status: str = "pending"  # pending / running / done / failed
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class SparcArtifact:
    """Tamamlanmış bir SPARC iterasyonunun nihai ürünü."""

    specification: str = ""
    pseudocode: str = ""
    architecture: str = ""
    refinement_log: List[str] = field(default_factory=list)
    completion_summary: str = ""
    files: Dict[str, str] = field(default_factory=dict)  # filename -> content


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------


class RufloSparc:
    """SPARC architecture assistant inspired by ruflo-sparc.

    Usage
    -----
    sparc = RufloSparc()
    artifact = await sparc.run(
        prompt="Build a REST API for a todo app",
        llm_call=my_llm_coro,
    )
    """

    PHASES = ["specification", "pseudocode", "architecture", "refinement", "completion"]

    def __init__(self) -> None:
        self.phases: List[SparcPhase] = []
        self._history: List[SparcArtifact] = []

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    async def run(
        self,
        prompt: str,
        llm_call: Callable[[str], Any],  # async or sync callable
        context: Optional[Dict[str, Any]] = None,
    ) -> SparcArtifact:
        """Execute the full SPARC pipeline.

        Parameters
        ----------
        prompt : str
            User requirement / feature description.
        llm_call : callable
            Receives a prompt string, returns a response string.
            Can be async or sync (wrapped automatically).
        context : dict
            Extra context injected into every phase.

        Returns
        -------
        ``SparcArtifact`` with outputs from all 5 phases.
        """
        artifact = SparcArtifact()
        self.phases = []
        ctx = dict(context or {})

        for phase_name in self.PHASES:
            phase = SparcPhase(name=phase_name)
            phase.input_data = {"prompt": prompt, "context": ctx}
            phase.status = "running"
            logger.info("[ruflo-sparc] phase %s started", phase_name)

            try:
                output = await self._invoke_llm(
                    llm_call,
                    self._build_phase_prompt(phase_name, prompt, artifact, ctx),
                )
                phase.status = "done"
                phase.output_data = {"response": output}
                self._apply_phase_output(phase_name, output, artifact)
            except Exception as exc:
                phase.status = "failed"
                phase.notes = str(exc)
                logger.exception("[ruflo-sparc] phase %s failed", phase_name)

            phase.status = phase.status
            self.phases.append(phase)

            if phase.status == "failed":
                break

        self._history.append(artifact)
        return artifact

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------

    def _build_phase_prompt(
        self,
        phase: str,
        prompt: str,
        artifact: SparcArtifact,
        context: Dict[str, Any],
    ) -> str:
        base = f"User request: {prompt}\n"
        if context:
            base += f"Context: {context}\n"

        prompts = {
            "specification": (
                base + "\n---\n"
                "PHASE 1 – SPECIFICATION\n"
                "Write a detailed specification: requirements, constraints,\n"
                "inputs, outputs, edge cases, and acceptance criteria.\n"
                "Respond in plain text / markdown."
            ),
            "pseudocode": (
                base + f"\n---\nSpecification:\n{artifact.specification}\n\n"
                "PHASE 2 – PSEUDOCODE\n"
                "Write high-level pseudocode / algorithm steps.\n"
                "Focus on logic, not syntax."
            ),
            "architecture": (
                base + f"\n---\nPseudocode:\n{artifact.pseudocode}\n\n"
                "PHASE 3 – ARCHITECTURE\n"
                "Propose a module / component breakdown.\n"
                "List files, classes, functions, and data flow."
            ),
            "refinement": (
                base + f"\n---\nArchitecture:\n{artifact.architecture}\n\n"
                "PHASE 4 – REFINEMENT\n"
                "Review the architecture for risks, missing tests,\n"
                "performance bottlenecks, and security concerns.\n"
                "Provide a list of improvements."
            ),
            "completion": (
                base + f"\n---\nRefinements:\n{artifact.refinement_log}\n\n"
                "PHASE 5 – COMPLETION\n"
                "Write a concise implementation plan and summary.\n"
                "If code generation is requested, emit file blocks:\n"
                "```filename.ext\n...content...\n```"
            ),
        }
        return prompts.get(phase, base)

    # ------------------------------------------------------------------
    # Apply outputs
    # ------------------------------------------------------------------

    def _apply_phase_output(self, phase: str, output: str, artifact: SparcArtifact) -> None:
        if phase == "specification":
            artifact.specification = output
        elif phase == "pseudocode":
            artifact.pseudocode = output
        elif phase == "architecture":
            artifact.architecture = output
        elif phase == "refinement":
            artifact.refinement_log = [line.strip() for line in output.splitlines() if line.strip()]
        elif phase == "completion":
            artifact.completion_summary = output
            artifact.files = self._extract_files(output)

    @staticmethod
    def _extract_files(text: str) -> Dict[str, str]:
        """Extract ```filename.ext blocks from LLM output."""
        import re

        files: Dict[str, str] = {}
        pattern = re.compile(r"```(\S+?)\n(.*?)```", re.DOTALL)
        for match in pattern.finditer(text):
            fname = match.group(1).strip()
            content = match.group(2).strip()
            if fname and content:
                files[fname] = content
        return files

    # ------------------------------------------------------------------
    # LLM wrapper
    # ------------------------------------------------------------------

    async def _invoke_llm(self, llm_call: Callable[[str], Any], prompt: str) -> str:
        import asyncio
        import inspect

        if inspect.iscoroutinefunction(llm_call):
            return await llm_call(prompt)
        # sync fallback — run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, llm_call, prompt)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get_phases(self) -> List[SparcPhase]:
        return list(self.phases)

    def last_artifact(self) -> Optional[SparcArtifact]:
        return self._history[-1] if self._history else None

    def status(self) -> Dict[str, Any]:
        return {
            "phases": [
                {"name": p.name, "status": p.status, "notes": p.notes}
                for p in self.phases
            ],
            "completed_runs": len(self._history),
        }
