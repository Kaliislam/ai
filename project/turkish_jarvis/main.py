"""FastAPI entry point — TurkishJARVIS v2.0 (Fully Integrated)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# v3.1 Skills Framework imports
try:
    from turkish_jarvis.skills.skill_registry_v2 import SkillRegistryV2
    from turkish_jarvis.skills.skill_loader import SkillLoader
except ImportError:
    pass


import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("jarvis.main")

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Kullanıcı mesajı")
    session_id: str = Field(default="", description="Oturum kimliği")
    enable_voice: bool = Field(default=False, description="Sesli yanıt")
    stream: bool = Field(default=False, description="Streaming yanıt")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Asistan yanıtı")
    session_id: str = Field(..., description="Oturum kimliği")
    tool_calls_used: list[str] = Field(default_factory=list)
    voice_url: str | None = Field(default=None)
    sources: list[dict] = Field(default_factory=list, description="RAG kaynakları")


class HealthResponse(BaseModel):
    status: str
    version: str
    modules: dict[str, str]
    timestamp: str


# ---------------------------------------------------------------------------
# Global module cache (set during lifespan)
# ---------------------------------------------------------------------------
_MODULES: dict[str, Any] = {}


def _get(name: str) -> Any:
    """Get a module from the global cache (may return None)."""
    return _MODULES.get(name)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama ömrü yönetimi: modülleri başlat ve kapat."""
    logger.info("=" * 60)
    logger.info("TurkishJARVIS v2.0 başlatılıyor...")
    logger.info("=" * 60)

    modules_status: dict[str, str] = {}

    # 1. Config
    try:
        from turkish_jarvis.config import JARVISConfig
        cfg = JARVISConfig()
        _MODULES["config"] = cfg
        modules_status["config"] = "ok"
        logger.info("✅ Config yüklendi: model=%s", cfg.ollama_model)
    except Exception as exc:
        modules_status["config"] = f"error: {exc}"
        logger.error("❌ Config yüklenemedi: %s", exc)
        yield
        return

    # 1.5 Ollama Process Manager
    try:
        from turkish_jarvis.core.ollama_manager import OllamaProcessManager
        ollama_mgr = OllamaProcessManager()
        ollama_port = ollama_mgr.start()
        _MODULES["ollama_manager"] = ollama_mgr
        modules_status["ollama_manager"] = f"ok (port {ollama_port})"
        # Update config with detected Ollama URL
        cfg.ollama_base_url = ollama_mgr.get_url()
        logger.info("✅ OllamaProcessManager hazır: %s", ollama_mgr.get_url())
    except Exception as exc:
        modules_status["ollama_manager"] = f"error: {exc}"
        logger.warning("⚠️ OllamaProcessManager yüklenemedi: %s", exc)

    # 1.5b Model Pool
    try:
        from turkish_jarvis.core.model_pool import OllamaModelPool
        model_pool = OllamaModelPool(base_url=cfg.ollama_base_url)
        _MODULES["model_pool"] = model_pool
        modules_status["model_pool"] = "ok"
        logger.info("✅ OllamaModelPool hazır (7 model).")
    except Exception as exc:
        modules_status["model_pool"] = f"error: {exc}"
        logger.warning("⚠️ ModelPool yüklenemedi: %s", exc)

    # 1.5c Council Manager (150+ ajan)
    try:
        from turkish_jarvis.agents.council_manager import CouncilManager
        council_mgr = CouncilManager(ollama_manager=ollama_mgr, model_pool=model_pool)
        _MODULES["council_manager"] = council_mgr
        modules_status["council_manager"] = "ok"
        logger.info("✅ CouncilManager hazır (182 ajan).")
    except Exception as exc:
        modules_status["council_manager"] = f"error: {exc}"
        logger.warning("⚠️ CouncilManager yüklenemedi: %s", exc)

    # 1.5d CEO Jarvis
    try:
        from turkish_jarvis.agents.executive.ceo import JarvisCEO
        ceo = JarvisCEO()
        ceo.council_manager = council_mgr
        _MODULES["ceo"] = ceo
        modules_status["ceo"] = "ok"
        logger.info("👑 CEO Jarvis hazır.")
    except Exception as exc:
        modules_status["ceo"] = f"error: {exc}"
        logger.warning("⚠️ CEO yüklenemedi: %s", exc)

    # 1.5e Register all 182 agents to councils
    try:
        from turkish_jarvis.agents import ALL_COUNCILS
        for dept, agents in ALL_COUNCILS.items():
            instances = [a() for a in agents]
            council_mgr.register_council(dept, instances)
        total_agents = sum(len(v) for v in ALL_COUNCILS.values())
        logger.info("🌐 %d ajan 19 council'e kaydedildi.", total_agents)
    except Exception as exc:
        logger.warning("⚠️ Ajan kaydı başarısız: %s", exc)
    except Exception as exc:
        modules_status["ollama_manager"] = f"error: {exc}"
        logger.warning("⚠️ OllamaProcessManager yüklenemedi: %s", exc)

    # 2. LLM Client
    try:
        from turkish_jarvis.core.llm import LLMClient
        llm = LLMClient(config=cfg)
        _MODULES["llm"] = llm
        modules_status["llm"] = "ok"
        logger.info("✅ LLM Client hazır.")
    except Exception as exc:
        modules_status["llm"] = f"error: {exc}"
        logger.error("❌ LLM Client yüklenemedi: %s", exc)

    # 3. Memory stores
    try:
        from turkish_jarvis.memory.conversation import ConversationStore
        conv = ConversationStore(db_path=cfg.sqlite_path)
        _MODULES["conversation_store"] = conv
        modules_status["conversation_store"] = "ok"
        logger.info("✅ ConversationStore hazır.")
    except Exception as exc:
        modules_status["conversation_store"] = f"error: {exc}"
        logger.error("❌ ConversationStore yüklenemedi: %s", exc)

    try:
        from turkish_jarvis.memory.episodic import EpisodicMemory
        epi = EpisodicMemory(persist_dir=cfg.chroma_persist_dir)
        _MODULES["episodic_memory"] = epi
        modules_status["episodic_memory"] = "ok"
        logger.info("✅ EpisodicMemory hazır.")
    except Exception as exc:
        modules_status["episodic_memory"] = f"error: {exc}"
        logger.warning("⚠️ EpisodicMemory yüklenemedi: %s", exc)

    try:
        from turkish_jarvis.memory.longterm import LongTermMemory
        lt = LongTermMemory(db_path=cfg.sqlite_path)
        _MODULES["long_term_memory"] = lt
        modules_status["long_term_memory"] = "ok"
        logger.info("✅ LongTermMemory hazır.")
    except Exception as exc:
        modules_status["long_term_memory"] = f"error: {exc}"
        logger.warning("⚠️ LongTermMemory yüklenemedi: %s", exc)

    try:
        from turkish_jarvis.memory.graph import GraphMemory
        graph = GraphMemory(db_path=cfg.sqlite_path)
        _MODULES["graph_memory"] = graph
        modules_status["graph_memory"] = "ok"
        logger.info("✅ GraphMemory hazır.")
    except Exception as exc:
        modules_status["graph_memory"] = f"error: {exc}"
        logger.warning("⚠️ GraphMemory yüklenemedi: %s", exc)

    # 4. RAG
    try:
        from turkish_jarvis.memory.rag import RAGPipeline
        rag = RAGPipeline(
            persist_dir=cfg.chroma_persist_dir,
            llm_client=_MODULES.get("llm"),
        )
        _MODULES["rag"] = rag
        modules_status["rag"] = "ok"
        logger.info("✅ RAG Pipeline hazır.")
    except Exception as exc:
        modules_status["rag"] = f"error: {exc}"
        logger.warning("⚠️ RAG Pipeline yüklenemedi: %s", exc)

    # 5. Tool Registry + builtin tools
    try:
        from turkish_jarvis.tools.registry import ToolRegistry
        from turkish_jarvis.tools import builtin
        registry = ToolRegistry()
        builtin.register_all(registry)
        _MODULES["tool_registry"] = registry
        modules_status["tool_registry"] = "ok"
        logger.info("✅ Tool Registry hazır (%d araç).", len(registry.get_schemas()))
    except Exception as exc:
        modules_status["tool_registry"] = f"error: {exc}"
        logger.error("❌ Tool Registry yüklenemedi: %s", exc)

    # 6. Personality
    try:
        from turkish_jarvis.personality.system_prompt import SystemPromptBuilder
        pb = SystemPromptBuilder(config=cfg)
        _MODULES["personality_builder"] = pb
        modules_status["personality"] = "ok"
        logger.info("✅ Personality hazır.")
    except Exception as exc:
        modules_status["personality"] = f"error: {exc}"
        logger.error("❌ Personality yüklenemedi: %s", exc)

    try:
        from turkish_jarvis.personality.proactive import ProactiveEngine
        proactive = ProactiveEngine(longterm=_MODULES.get("long_term_memory"))
        _MODULES["proactive"] = proactive
        modules_status["proactive"] = "ok"
        logger.info("✅ Proactive Engine hazır.")
    except Exception as exc:
        modules_status["proactive"] = f"error: {exc}"
        logger.warning("⚠️ Proactive Engine yüklenemedi: %s", exc)

    # 7. STT / TTS / Streaming
    try:
        from turkish_jarvis.core.stt import STTClient
        stt = STTClient(model_size=cfg.stt_model)
        _MODULES["stt"] = stt
        modules_status["stt"] = "ok"
        logger.info("✅ STT hazır.")
    except Exception as exc:
        modules_status["stt"] = f"error: {exc}"
        logger.warning("⚠️ STT yüklenemedi: %s", exc)

    try:
        from turkish_jarvis.core.tts import TTSClient
        tts = TTSClient(
            model_path=cfg.tts_model_path,
            config_path=cfg.tts_config_path,
        )
        _MODULES["tts"] = tts
        modules_status["tts"] = "ok"
        logger.info("✅ TTS hazır.")
    except Exception as exc:
        modules_status["tts"] = f"error: {exc}"
        logger.warning("⚠️ TTS yüklenemedi: %s", exc)

    try:
        from turkish_jarvis.core.streaming import StreamingPipeline
        streaming = StreamingPipeline(llm=_MODULES.get("llm"), tts=_MODULES.get("tts"))
        _MODULES["streaming"] = streaming
        modules_status["streaming"] = "ok"
        logger.info("✅ Streaming Pipeline hazır.")
    except Exception as exc:
        modules_status["streaming"] = f"error: {exc}"
        logger.warning("⚠️ Streaming Pipeline yüklenemedi: %s", exc)

    # 8. Integrations (optional)
    # MCP Client
    try:
        from turkish_jarvis.integrations.mcp_client import MCPClient
        mcp = MCPClient()
        _MODULES["mcp"] = mcp
        modules_status["mcp"] = "ok"
        logger.info("✅ MCP Client hazır.")
    except Exception as exc:
        modules_status["mcp"] = f"error: {exc}"
        logger.warning("⚠️ MCP Client yüklenemedi: %s", exc)

    # Home Assistant
    try:
        from turkish_jarvis.integrations.home_assistant import HomeAssistantClient
        ha_url = os.getenv("HOME_ASSISTANT_URL", "")
        ha_token = os.getenv("HOME_ASSISTANT_TOKEN", "")
        if ha_url and ha_token:
            ha = HomeAssistantClient(base_url=ha_url, token=ha_token)
            _MODULES["home_assistant"] = ha
            modules_status["home_assistant"] = "ok"
            logger.info("✅ Home Assistant entegrasyonu hazır.")
        else:
            modules_status["home_assistant"] = "skipped (no config)"
            logger.info("ℹ️ Home Assistant yapılandırılmamış — atlandı.")
    except Exception as exc:
        modules_status["home_assistant"] = f"error: {exc}"
        logger.warning("⚠️ Home Assistant yüklenemedi: %s", exc)

    # Browser
    try:
        from turkish_jarvis.integrations.browser import BrowserClient
        browser = BrowserClient()
        _MODULES["browser"] = browser
        modules_status["browser"] = "ok"
        logger.info("✅ Browser Client hazır.")
    except Exception as exc:
        modules_status["browser"] = f"error: {exc}"
        logger.warning("⚠️ Browser Client yüklenemedi: %s", exc)

    # 9. Meta Learning Engine
    try:
        from turkish_jarvis.autonomy.meta_learning import MetaLearningEngine
        ml = MetaLearningEngine(db_path=cfg.sqlite_path.replace(".db", "_meta.db"))
        _MODULES["meta_learning"] = ml
        modules_status["meta_learning"] = "ok"
        logger.info("✅ MetaLearningEngine hazır.")
    except Exception as exc:
        modules_status["meta_learning"] = f"error: {exc}"
        logger.warning("⚠️ MetaLearningEngine yüklenemedi: %s", exc)


    # 9.5 Planner (autonomy)
    try:
        from turkish_jarvis.autonomy.planner import TaskPlanner
        planner = TaskPlanner(llm_client=_MODULES.get("llm"), tool_registry=_MODULES.get("tool_registry"))
        _MODULES["planner"] = planner
        modules_status["planner"] = "ok"
        logger.info("✅ TaskPlanner (autonomy) hazır.")
    except Exception as exc:
        modules_status["planner"] = f"error: {exc}"
        logger.warning("⚠️ TaskPlanner yüklenemedi: %s", exc)

    # 9.6 Auto-Skill Generator (autonomy)
    try:
        from turkish_jarvis.autonomy.auto_skill import AutoSkillGenerator
        auto_skill = AutoSkillGenerator(
            llm_client=_MODULES.get("llm"),
            tool_registry=_MODULES.get("tool_registry"),
            project_dir=str(Path(__file__).resolve().parent.parent),
        )
        _MODULES["auto_skill"] = auto_skill
        modules_status["auto_skill"] = "ok"
        logger.info("✅ AutoSkillGenerator hazır.")
    except Exception as exc:
        modules_status["auto_skill"] = f"error: {exc}"
        logger.warning("⚠️ AutoSkillGenerator yüklenemedi: %s", exc)

    # 9.7 Knowledge Miner (autonomy)
    try:
        from turkish_jarvis.autonomy.knowledge_miner import KnowledgeMiner
        miner = KnowledgeMiner(rag_pipeline=_MODULES.get("rag"), llm_client=_MODULES.get("llm"))
        _MODULES["knowledge_miner"] = miner
        modules_status["knowledge_miner"] = "ok"
        logger.info("✅ KnowledgeMiner hazır.")
    except Exception as exc:
        modules_status["knowledge_miner"] = f"error: {exc}"
        logger.warning("⚠️ KnowledgeMiner yüklenemedi: %s", exc)

    # 9.8 Reflection Engine (autonomy)
    try:
        from turkish_jarvis.autonomy.reflection import ReflectionEngine
        reflection = ReflectionEngine(llm_client=_MODULES.get("llm"))
        _MODULES["reflection"] = reflection
        modules_status["reflection"] = "ok"
        logger.info("✅ ReflectionEngine hazır.")
    except Exception as exc:
        modules_status["reflection"] = f"error: {exc}"
        logger.warning("⚠️ ReflectionEngine yüklenemedi: %s", exc)

    # 9.9 Self-Healing Engine (autonomy)
    try:
        from turkish_jarvis.autonomy.self_healing import SelfHealingEngine
        healing = SelfHealingEngine(llm_client=_MODULES.get("llm"))
        _MODULES["self_healing"] = healing
        modules_status["self_healing"] = "ok"
        logger.info("✅ SelfHealingEngine hazır.")
    except Exception as exc:
        modules_status["self_healing"] = f"error: {exc}"
        logger.warning("⚠️ SelfHealingEngine yüklenemedi: %s", exc)

    # 9.10 Skills Framework v2
    try:
        from turkish_jarvis.skills.skill_registry_v2 import SkillRegistryV2
        from turkish_jarvis.skills.skill_loader import SkillLoader
        skill_reg_v2 = SkillRegistryV2()
        skill_loader = SkillLoader(skill_reg_v2)
        _MODULES["skill_registry_v2"] = skill_reg_v2
        _MODULES["skill_loader"] = skill_loader
        modules_status["skill_registry_v2"] = "ok"
        logger.info("✅ SkillRegistryV2 hazır.")
    except Exception as exc:
        modules_status["skill_registry_v2"] = f"error: {exc}"
        logger.warning("⚠️ SkillRegistryV2 yüklenemedi: %s", exc)

    # 9.10b Unified Skill Manager (tüm repolar)
    try:
        from turkish_jarvis.skills.unified_manager import UnifiedSkillManager
        unified_mgr = UnifiedSkillManager(skill_registry=skill_reg_v2)
        _MODULES["unified_skill_manager"] = unified_mgr
        modules_status["unified_skill_manager"] = "ok"
        logger.info("✅ UnifiedSkillManager hazır (4 repo desteği).")
    except Exception as exc:
        modules_status["unified_skill_manager"] = f"error: {exc}"
        logger.warning("⚠️ UnifiedSkillManager yüklenemedi: %s", exc)

    # 9.10c Free Search Engine (API-key'siz internet arama)
    try:
        from turkish_jarvis.skills.web.free_search import FreeSearchEngine
        free_search_engine = FreeSearchEngine()
        _MODULES["free_search_engine"] = free_search_engine
        modules_status["free_search_engine"] = "ok"
        logger.info("✅ FreeSearchEngine hazır (DuckDuckGo/SearXNG/Bing).")
    except Exception as exc:
        modules_status["free_search_engine"] = f"error: {exc}"
        logger.warning("⚠️ FreeSearchEngine yüklenemedi: %s", exc)

    # 9.10d Ruflo Bridge (opsiyonel)
    try:
        from turkish_jarvis.skills.ruflo_bridge import (
            RufloBrowserBridge, RufloSwarm, RufloAutopilot,
            RufloGoals, RufloObservability, RufloSecurityAudit,
            RufloSparc, RufloLoopWorkers, RufloMarketData,
        )
        _MODULES["ruflo_browser"] = RufloBrowserBridge()
        _MODULES["ruflo_swarm"] = RufloSwarm()
        _MODULES["ruflo_autopilot"] = RufloAutopilot()
        _MODULES["ruflo_goals"] = RufloGoals()
        modules_status["ruflo_bridge"] = "ok"
        logger.info("✅ Ruflo Bridge hazır (12 plugin).")
    except Exception as exc:
        modules_status["ruflo_bridge"] = f"error: {exc}"
        logger.warning("⚠️ Ruflo Bridge yüklenemedi: %s", exc)

    # 9.10e Claude Skills (opsiyonel)
    try:
        from turkish_jarvis.skills.claude_skills.skill_adapter import ClaudeSkillAdapter
        claude_adapter = ClaudeSkillAdapter(llm_client=_MODULES.get("llm"))
        _MODULES["claude_skill_adapter"] = claude_adapter
        modules_status["claude_skills"] = "ok"
        logger.info("✅ ClaudeSkillAdapter hazır (16 skill).")
    except Exception as exc:
        modules_status["claude_skills"] = f"error: {exc}"
        logger.warning("⚠️ ClaudeSkillAdapter yüklenemedi: %s", exc)
    except Exception as exc:
        modules_status["skill_registry_v2"] = f"error: {exc}"
        logger.warning("⚠️ SkillRegistryV2 yüklenemedi: %s", exc)

    # 9.11 Chat History Manager
    try:
        from turkish_jarvis.skills.system.chat_history import ChatHistoryManager
        chat_history = ChatHistoryManager(db_path=cfg.sqlite_path)
        _MODULES["chat_history"] = chat_history
        modules_status["chat_history"] = "ok"
        logger.info("✅ ChatHistoryManager hazır.")
    except Exception as exc:
        modules_status["chat_history"] = f"error: {exc}"
        logger.warning("⚠️ ChatHistoryManager yüklenemedi: %s", exc)

    # 9.12 Conversation Indexer
    try:
        from turkish_jarvis.skills.system.conversation_indexer import ConversationIndexer
        conv_indexer = ConversationIndexer(chroma_dir=cfg.chroma_persist_dir)
        _MODULES["conversation_indexer"] = conv_indexer
        modules_status["conversation_indexer"] = "ok"
        logger.info("✅ ConversationIndexer hazır.")
    except Exception as exc:
        modules_status["conversation_indexer"] = f"error: {exc}"
        logger.warning("⚠️ ConversationIndexer yüklenemedi: %s", exc)

    # 9.13 Project Manager
    try:
        from turkish_jarvis.skills.system.project_manager import ProjectManager
        project_mgr = ProjectManager(db_path=cfg.sqlite_path)
        _MODULES["project_manager"] = project_mgr
        modules_status["project_manager"] = "ok"
        logger.info("✅ ProjectManager hazır.")
    except Exception as exc:
        modules_status["project_manager"] = f"error: {exc}"
        logger.warning("⚠️ ProjectManager yüklenemedi: %s", exc)

    # 9.14 Todo Manager
    try:
        from turkish_jarvis.skills.system.todo_manager import TodoManager
        todo_mgr = TodoManager(db_path=cfg.sqlite_path)
        _MODULES["todo_manager"] = todo_mgr
        modules_status["todo_manager"] = "ok"
        logger.info("✅ TodoManager hazır.")
    except Exception as exc:
        modules_status["todo_manager"] = f"error: {exc}"
        logger.warning("⚠️ TodoManager yüklenemedi: %s", exc)

    # 9.15 Instruction Manager
    try:
        from turkish_jarvis.skills.system.instruction_manager import InstructionManager
        instruction_mgr = InstructionManager(db_path=cfg.sqlite_path)
        _MODULES["instruction_manager"] = instruction_mgr
        modules_status["instruction_manager"] = "ok"
        logger.info("✅ InstructionManager hazır.")
    except Exception as exc:
        modules_status["instruction_manager"] = f"error: {exc}"
        logger.warning("⚠️ InstructionManager yüklenemedi: %s", exc)

    # 9.16 Web Search Advanced
    try:
        from turkish_jarvis.skills.web.web_search_advanced import WebSearchSkill
        web_search = WebSearchSkill()
        _MODULES["web_search"] = web_search
        modules_status["web_search"] = "ok"
        logger.info("✅ WebSearchSkill hazır.")
    except Exception as exc:
        modules_status["web_search"] = f"error: {exc}"
        logger.warning("⚠️ WebSearchSkill yüklenemedi: %s", exc)

    # 9.17 Info Refresh
    try:
        from turkish_jarvis.skills.web.info_refresh import InfoRefreshSkill
        info_refresh = InfoRefreshSkill()
        _MODULES["info_refresh"] = info_refresh
        modules_status["info_refresh"] = "ok"
        logger.info("✅ InfoRefreshSkill hazır.")
    except Exception as exc:
        modules_status["info_refresh"] = f"error: {exc}"
        logger.warning("⚠️ InfoRefreshSkill yüklenemedi: %s", exc)

    # 9.18 RSS Reader
    try:
        from turkish_jarvis.skills.web.rss_reader import RSSReaderSkill
        rss_reader = RSSReaderSkill()
        _MODULES["rss_reader"] = rss_reader
        modules_status["rss_reader"] = "ok"
        logger.info("✅ RSSReaderSkill hazır.")
    except Exception as exc:
        modules_status["rss_reader"] = f"error: {exc}"
        logger.warning("⚠️ RSSReaderSkill yüklenemedi: %s", exc)

    # 10. Kullanıcı profili yükle
    try:
        profile_path = Path("data/user_profile.md")
        if profile_path.exists():
            _MODULES["user_profile"] = profile_path.read_text(encoding="utf-8")
            modules_status["user_profile"] = "loaded"
            logger.info("✅ Kullanıcı profili yüklendi.")
        else:
            modules_status["user_profile"] = "not found"
            logger.info("ℹ️ Kullanıcı profili bulunamadı.")
    except Exception as exc:
        modules_status["user_profile"] = f"error: {exc}"
        logger.warning("⚠️ Kullanıcı profili yüklenemedi: %s", exc)

    app.state.jarvis_modules = modules_status
    app.state.config = cfg

    logger.info("=" * 60)
    logger.info("Başlatma tamamlandı — %d/%d modül hazır.",
                sum(1 for v in modules_status.values() if v == "ok"),
                len(modules_status))
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("TurkishJARVIS kapatılıyor...")
    for key in ("conversation_store", "episodic_memory", "long_term_memory",
                "graph_memory", "rag", "meta_learning", "mcp", "home_assistant", "browser"):
        inst = _MODULES.get(key)
        if inst and hasattr(inst, "close"):
            try:
                if asyncio.iscoroutinefunction(inst.close):
                    await inst.close()
                else:
                    inst.close()
            except Exception as exc:
                logger.warning("Kapatma hatası (%s): %s", key, exc)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TurkishJARVIS API v2.0",
    description="Kişisel AI Asistanı — FastAPI + Gradio + WebSocket + MCP + Streaming",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Include API v2 router
# ---------------------------------------------------------------------------

try:
    from turkish_jarvis.api.endpoints import router as api_v2_router
    app.include_router(api_v2_router, prefix="/api/v2")
    logger.info("✅ API v2 router yüklendi.")
except Exception as exc:
    logger.warning("⚠️ API v2 router yüklenemedi: %s", exc)


# ---------------------------------------------------------------------------
# Helper: Build chat context
# ---------------------------------------------------------------------------

async def _build_chat_context(
    session_id: str,
    user_message: str,
) -> tuple[list[dict], list[dict], str]:
    """Build messages, tools, and system prompt for a chat turn.

    Returns:
        (messages_list, tool_schemas, system_prompt)
    """
    cfg = _get("config")
    conv = _get("conversation_store")
    episodic = _get("episodic_memory")
    longterm = _get("long_term_memory")
    graph = _get("graph_memory")
    rag = _get("rag")
    tools_reg = _get("tool_registry")
    personality = _get("personality_builder")

    # 1. History
    history: list[dict] = []
    if conv is not None:
        try:
            history = conv.get_history(session_id, limit=20)
        except Exception:
            logger.exception("History fetch error")

    # 2. Episodic memory
    episodic_context = ""
    if episodic is not None:
        try:
            memories = episodic.search(user_message, k=3)
            if memories:
                episodic_context = "\n".join(
                    f"- {m.get('text', m)}" for m in memories
                )
        except Exception:
            logger.exception("Episodic search error")

    # 3. Graph memory
    graph_context = ""
    if graph is not None:
        try:
            related = graph.search_related(user_message)
            if related:
                graph_context = "\n".join(
                    f"- {r.get('name', r)}: {r.get('attributes', {})}" for r in related
                )
        except Exception:
            logger.exception("Graph memory error")

    # 4. RAG context
    rag_context = ""
    if rag is not None:
        try:
            rag_results = rag.query_with_sources(user_message, k=3)
            if rag_results:
                rag_context = "\n".join(
                    f"- [{r.get('source', 'bilinmiyor')}] {r.get('content', '')[:200]}"
                    for r in rag_results
                )
        except Exception:
            logger.exception("RAG query error")

    # 5. Preferences
    user_prefs: dict = {}
    if longterm is not None:
        try:
            user_prefs = longterm.get_all_preferences(session_id)
        except Exception:
            logger.exception("Preferences fetch error")

    # 6. User profile
    profile_text = _MODULES.get("user_profile", "")

    # 7. Tools
    tool_schemas: list[dict] = []
    if tools_reg is not None:
        try:
            tool_schemas = tools_reg.get_schemas()
        except Exception:
            logger.exception("Tool schemas error")

    # 8. System prompt
    memory_parts = [episodic_context, graph_context, rag_context]
    memory_context = "\n\n".join(p for p in memory_parts if p)

    system_prompt = f"Sen TurkishJARVIS'sin. Kullanıcıya yardımcı ol."
    if personality is not None:
        try:
            system_prompt = personality.build(
                user_preferences=user_prefs,
                memory_context=memory_context,
                tool_schemas=tool_schemas,
                language="tr",
                user_profile=profile_text,
            )
        except Exception:
            logger.exception("System prompt build error")

    # 8.5 Meta-learning prompt optimization
    meta_learning = _get("meta_learning")
    if meta_learning is not None:
        try:
            system_prompt = meta_learning.optimize_prompt(system_prompt)
        except Exception:
            logger.exception("Meta-learning optimize_prompt error")

    # 9. Messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    return messages, tool_schemas, system_prompt


# ---------------------------------------------------------------------------
# Helper: Execute tool calls
# ---------------------------------------------------------------------------

async def _execute_tool_calls(
    tool_calls: list[dict],
    messages: list[dict],
) -> tuple[str, list[str]]:
    """Execute tool calls and re-call LLM if needed.

    Returns:
        (final_content, tool_names_used)
    """
    tools_reg = _get("tool_registry")
    llm = _get("llm")
    tool_schemas = tools_reg.get_schemas() if tools_reg else []
    tool_names_used: list[str] = []

    if not tool_calls or tools_reg is None:
        return "", tool_names_used

    for tc in tool_calls:
        name = ""
        arguments = {}
        if isinstance(tc, dict):
            fn = tc.get("function", tc)
            name = fn.get("name", "") if isinstance(fn, dict) else getattr(fn, "name", "")
            args = fn.get("arguments", {}) if isinstance(fn, dict) else getattr(fn, "arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            arguments = args if isinstance(args, dict) else {}
        else:
            continue

        if not name:
            continue

        try:
            result = await tools_reg.execute(name, arguments)
            tool_names_used.append(name)
            messages.append({
                "role": "tool",
                "name": name,
                "content": str(result)[:4000],
            })
            logger.info("🔧 Araç çalıştırıldı: %s -> %s", name, str(result)[:100])
        except Exception as exc:
            logger.exception("Tool execution error: %s", name)
            # Self-healing attempt
            healing = _get("self_healing")
            if healing is not None:
                try:
                    func = tools_reg._tools.get(name)
                    if func is not None:
                        hr = await healing.heal_tool_error(func, arguments, exc, traceback.format_exc())
                        if hr.success and hr.test_passed:
                            logger.info("🩹 Self-healing başarılı: %s", name)
                            # Try again with healed tool
                            try:
                                result = await tools_reg.execute(name, arguments)
                                tool_names_used.append(name)
                                messages.append({
                                    "role": "tool",
                                    "name": name,
                                    "content": str(result)[:4000],
                                })
                                continue
                            except Exception:
                                logger.warning("Healed tool still failing: %s", name)
                except Exception:
                    logger.exception("Self-healing error")
            messages.append({
                "role": "tool",
                "name": name,
                "content": f"Araç çalıştırma hatası: {exc}",
            })

    # Re-call LLM with tool results
    if llm is not None:
        try:
            llm_result = await llm.chat(messages, tools=tool_schemas or None)
            return llm_result.get("content", ""), tool_names_used
        except Exception as exc:
            logger.exception("LLM re-chat error")
            return f"Araç sonuçları işlenirken hata: {exc}", tool_names_used

    return "", tool_names_used


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check() -> dict:
    """Sağlık durumu ve modül durumlarını döndür."""
    modules = getattr(app.state, "jarvis_modules", {})
    ok_count = sum(1 for v in modules.values() if v == "ok")
    total = len(modules)
    return {
        "status": "healthy" if ok_count == total else "degraded",
        "version": "2.0.0",
        "modules": modules,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> dict:
    """HTTP tabanlı chat endpoint'i.

    Request:
        {"message": "...", "session_id": "...", "enable_voice": false, "stream": false}
    Response:
        {"response": "...", "session_id": "...", "tool_calls_used": [...], "voice_url": null, "sources": []}
    """
    llm = _get("llm")
    if llm is None:
        raise HTTPException(status_code=503, detail="LLM istemcisi hazır değil.")

    session_id = request.session_id or str(uuid.uuid4())

    # Build context
    messages, tool_schemas, _ = await _build_chat_context(session_id, request.message)

    # LLM call
    t0 = time.perf_counter()
    try:
        llm_result = await llm.chat(messages, tools=tool_schemas or None)
    except Exception as exc:
        logger.exception("LLM chat error")
        raise HTTPException(status_code=503, detail=f"LLM hatası: {exc}")
    latency_ms = (time.perf_counter() - t0) * 1000

    content = llm_result.get("content", "")
    tool_calls = llm_result.get("tool_calls") or []
    tool_names_used: list[str] = []

    # Tool execution
    if tool_calls:
        t1 = time.perf_counter()
        content, tool_names_used = await _execute_tool_calls(tool_calls, messages)
        latency_ms += (time.perf_counter() - t1) * 1000

    # Save conversation
    conv = _get("conversation_store")
    if conv is not None:
        try:
            conv.add_message(session_id, "user", request.message)
            conv.add_message(session_id, "assistant", content, tool_calls=tool_names_used)
        except Exception:
            logger.exception("Conversation save error")

    # v3.1: Chat History (comprehensive)
    chat_history = _get("chat_history")
    if chat_history is not None:
        try:
            chat_history.save_message(session_id, "user", request.message,
                                      metadata={"tools_used": tool_names_used, "model": getattr(_get("llm"), "model", "unknown")})
            chat_history.save_message(session_id, "assistant", content,
                                      metadata={"tools_used": tool_names_used, "sources": [s.get("source") for s in sources]})
            # Auto-extract facts and preferences
            conv_indexer = _get("conversation_indexer")
            if conv_indexer is not None:
                facts = conv_indexer.extract_facts(session_id)
                if facts:
                    logger.info("📋 %d fact extracted from session", len(facts))
                prefs = conv_indexer.extract_preferences(session_id)
                if prefs:
                    logger.info("💡 %d preference extracted from session", len(prefs))
        except Exception:
            logger.exception("Chat history save error")

    # Episodic memory (save important info)
    episodic = _get("episodic_memory")
    if episodic is not None:
        try:
            if len(content) > 50 or tool_names_used:
                episodic.add(
                    text=f"User: {request.message}\nAssistant: {content[:200]}",
                    metadata={"session_id": session_id, "tools": tool_names_used},
                )
        except Exception:
            logger.exception("Episodic save error")

    # Proactive learning
    proactive = _get("proactive")
    if proactive is not None:
        try:
            proactive.learn_from_message(session_id, request.message)
        except Exception:
            logger.exception("Proactive learning error")

    # Meta-learning log
    cfg = _get("config")
    meta_learning = _get("meta_learning")
    if meta_learning is not None:
        try:
            meta_learning.log_interaction(
                session_id=session_id,
                objective=request.message,
                tools_used=tool_names_used,
                model=cfg.ollama_model if cfg else "unknown",
                prompt_version="default",
                success=bool(content.strip()),
                latency=latency_ms,
            )
        except Exception:
            logger.exception("Meta-learning log error")

    # TTS
    voice_url: str | None = None
    if request.enable_voice:
        tts = _get("tts")
        if tts is not None and content:
            try:
                voice_path = await tts.synthesize(content)
                if voice_path and os.path.exists(voice_path):
                    voice_url = voice_path
            except Exception:
                logger.exception("TTS error")

    # 11. Reflection — yanıtı iyileştir
    reflection = _get("reflection")
    if reflection is not None and content:
        try:
            refl_result = await reflection.reflect_and_answer(
                question=request.message,
                context={"tools_used": tool_names_used, "sources": sources},
            )
            if refl_result.final_evaluation.overall_score > refl_result.initial_response and len(refl_result.final_response) > 10:
                content = refl_result.final_response
                logger.info("🪞 Reflection ile yanıt iyileştirildi (score: %.2f)", refl_result.final_evaluation.overall_score)
        except Exception:
            logger.exception("Reflection error")

    # 12. Auto-skill — bilinmeyen görev varsa yeni yetenek edin
    auto_skill = _get("auto_skill")
    if auto_skill is not None and not content.strip() and not tool_names_used:
        try:
            skill_result = await auto_skill.acquire_skill(request.message)
            if skill_result.success:
                content = f"Yeni bir yetenek öğrendim efendim: {skill_result.skill_name}. Bir daha deneyebilirsiniz."
                logger.info("🎓 Auto-skill başarılı: %s", skill_result.skill_name)
        except Exception:
            logger.exception("Auto-skill error")

    # Sources (RAG + Free Web Search)
    sources: list[dict] = []
    rag = _get("rag")
    if rag is not None:
        try:
            rag_results = rag.query_with_sources(request.message, k=3)
            sources = [
                {"content": r.get("content", "")[:200], "source": r.get("source", "bilinmiyor")}
                for r in rag_results
            ]
        except Exception:
            pass

    # Free web search fallback (if no RAG sources found)
    if not sources:
        free_search = _get("free_search_engine")
        if free_search is not None:
            try:
                web_results = await free_search.search(request.message, max_results=3)
                sources = [
                    {"content": r.snippet[:200], "source": r.source, "url": r.url}
                    for r in web_results[:3]
                ]
                logger.info("🌐 Free web search: %d results", len(sources))
            except Exception:
                logger.debug("Free search fallback failed")

    return {
        "response": content,
        "session_id": session_id,
        "tool_calls_used": tool_names_used,
        "voice_url": voice_url,
        "sources": sources,
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming chat endpoint."""
    llm = _get("llm")
    if llm is None:
        raise HTTPException(status_code=503, detail="LLM istemcisi hazır değil.")

    t0 = time.perf_counter()
    session_id = request.session_id or str(uuid.uuid4())
    messages, tool_schemas, _ = await _build_chat_context(session_id, request.message)

    from fastapi.responses import StreamingResponse

    async def _event_generator():
        full_content = ""
        async for chunk in llm.stream_chat(messages):
            full_content += chunk
            yield f"data: {json.dumps({'chunk': chunk, 'session_id': session_id})}\n\n"

        latency_ms = (time.perf_counter() - t0) * 1000

        # Save conversation after streaming
        conv = _get("conversation_store")
        if conv is not None:
            try:
                conv.add_message(session_id, "user", request.message)
                conv.add_message(session_id, "assistant", full_content)
            except Exception:
                logger.exception("Conversation save error")

        # Meta-learning log
        cfg = _get("config")
        meta_learning = _get("meta_learning")
        if meta_learning is not None:
            try:
                meta_learning.log_interaction(
                    session_id=session_id,
                    objective=request.message,
                    tools_used=[],
                    model=cfg.ollama_model if cfg else "unknown",
                    prompt_version="default",
                    success=bool(full_content.strip()),
                    latency=latency_ms,
                )
            except Exception:
                logger.exception("Meta-learning log error (stream)")

        yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'response': full_content})}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time WebSocket chat endpoint'i."""
    from turkish_jarvis.ui.websocket import WebSocketManager

    ws_manager = WebSocketManager(
        llm_client=_get("llm"),
        conversation_store=_get("conversation_store"),
        episodic_memory=_get("episodic_memory"),
        long_term_memory=_get("long_term_memory"),
        rag=_get("rag"),
        tool_registry=_get("tool_registry"),
        personality_builder=_get("personality_builder"),
        stt_engine=_get("stt"),
        tts_engine=_get("tts"),
    )
    await ws_manager.handle(websocket)


# ---------------------------------------------------------------------------
# Gradio mount
# ---------------------------------------------------------------------------

_gradio_app: Any | None = None


def _get_gradio_app() -> Any:
    """Gradio Blocks uygulamasını lazily oluştur."""
    global _gradio_app
    if _gradio_app is not None:
        return _gradio_app

    from turkish_jarvis.ui.gradio_app import GradioUI

    ui = GradioUI(
        config=_get("config"),
        llm_client=_get("llm"),
        conversation_store=_get("conversation_store"),
        episodic_memory=_get("episodic_memory"),
        long_term_memory=_get("long_term_memory"),
        rag=_get("rag"),
        tool_registry=_get("tool_registry"),
        personality_builder=_get("personality_builder"),
        stt_engine=_get("stt"),
        tts_engine=_get("tts"),
    )
    _gradio_app = ui.build()
    return _gradio_app


import gradio as gr

gradio_blocks = _get_gradio_app()
if gradio_blocks is not None:
    app = gr.mount_gradio_app(app, gradio_blocks, path="/ui")
    logger.info("🎨 Gradio UI /ui altına mount edildi.")


# ---------------------------------------------------------------------------
# Uvicorn entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.getenv("JARVIS_HOST", "0.0.0.0")
    port = int(os.getenv("JARVIS_PORT", "8000"))
    reload = os.getenv("JARVIS_RELOAD", "false").lower() == "true"

    logger.info("🚀 Uvicorn başlatılıyor: %s:%d", host, port)
    uvicorn.run(
        "turkish_jarvis.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
