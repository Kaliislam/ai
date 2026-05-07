"""TurkishJARVIS Agent Swarm — 150+ uzman ajan."""

from __future__ import annotations

from .base_agent import BaseAgent

# ───────────────────────────────────────────
# Tools Council (15)
# ───────────────────────────────────────────
from .tools.calculator_agent import CalculatorAgent
from .tools.converter_agent import ConverterAgent
from .tools.formatter_agent import FormatterAgent
from .tools.validator_agent import ValidatorAgent
from .tools.parser_agent import ParserAgent
from .tools.generator_agent import GeneratorAgent
from .tools.builder_agent import BuilderAgent
from .tools.deployer_agent import DeployerAgent
from .tools.tester_agent import TesterAgent
from .tools.debugger_agent import DebuggerAgent
from .tools.profiler_agent import ProfilerAgent
from .tools.optimizer_agent import OptimizerAgent
from .tools.cleaner_agent import CleanerAgent
from .tools.backup_agent import BackupAgent
from .tools.restorer_agent import RestorerAgent

# ───────────────────────────────────────────
# Meta Council (15)
# ───────────────────────────────────────────
from .meta.self_improvement_agent import SelfImprovementAgent
from .meta.learning_agent import LearningAgent
from .meta.memory_agent import MemoryAgent
from .meta.reflection_agent import ReflectionAgent
from .meta.planning_agent import PlanningAgent
from .meta.execution_agent import ExecutionAgent
from .meta.coordination_agent import CoordinationAgent
from .meta.communication_agent import CommunicationAgent
from .meta.negotiation_agent import NegotiationAgent
from .meta.decision_agent import DecisionAgent
from .meta.priority_agent import PriorityAgent
from .meta.resource_agent import ResourceAgent
from .meta.conflict_agent import ConflictAgent
from .meta.quality_agent import QualityAgent
from .meta.performance_agent import PerformanceAgent

# ───────────────────────────────────────────
# AI Action Council (10)
# ───────────────────────────────────────────
from .ai_action.prompt_engineer_agent import PromptEngineerAgent
from .ai_action.model_selector_agent import ModelSelectorAgent
from .ai_action.inference_agent import InferenceAgent
from .ai_action.embedding_agent import EmbeddingAgent
from .ai_action.tokenizer_agent import TokenizerAgent
from .ai_action.fine_tuner_agent import FineTunerAgent
from .ai_action.evaluator_agent import EvaluatorAgent
from .ai_action.benchmark_agent import BenchmarkAgent
from .ai_action.dataset_agent import DatasetAgent
from .ai_action.pipeline_agent import PipelineAgent

# ───────────────────────────────────────────
# Tüm council'lerin listesi
# ───────────────────────────────────────────
ALL_COUNCILS = {
    "tools": [
        CalculatorAgent,
        ConverterAgent,
        FormatterAgent,
        ValidatorAgent,
        ParserAgent,
        GeneratorAgent,
        BuilderAgent,
        DeployerAgent,
        TesterAgent,
        DebuggerAgent,
        ProfilerAgent,
        OptimizerAgent,
        CleanerAgent,
        BackupAgent,
        RestorerAgent,
    ],
    "meta": [
        SelfImprovementAgent,
        LearningAgent,
        MemoryAgent,
        ReflectionAgent,
        PlanningAgent,
        ExecutionAgent,
        CoordinationAgent,
        CommunicationAgent,
        NegotiationAgent,
        DecisionAgent,
        PriorityAgent,
        ResourceAgent,
        ConflictAgent,
        QualityAgent,
        PerformanceAgent,
    ],
    "ai_action": [
        PromptEngineerAgent,
        ModelSelectorAgent,
        InferenceAgent,
        EmbeddingAgent,
        TokenizerAgent,
        FineTunerAgent,
        EvaluatorAgent,
        BenchmarkAgent,
        DatasetAgent,
        PipelineAgent,
    ],
}

# Toplam ajan sayısı (mevcut council'ler)
AGENT_COUNT = sum(len(v) for v in ALL_COUNCILS.values())
