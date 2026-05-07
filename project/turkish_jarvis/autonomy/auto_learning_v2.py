"""Auto-Learning Engine v2 — kendi kendine gelişen AI."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("jarvis.auto_learning_v2")


@dataclass
class LearningEntry:
    """Tek bir öğrenme döngüsünün kaydı."""
    timestamp: str
    topics: List[str]
    new_skills: List[str] = field(default_factory=list)
    perf_metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


class AutoLearningEngine:
    """Asistanın kendi kendini geliştirmesini sağlayan motor."""

    def __init__(
        self,
        search_engine=None,
        rag_pipeline=None,
        knowledge_miner=None,
        meta_learning=None,
        topic_tracker=None,
        learning_interval_hours: int = 6,
    ):
        self.search = search_engine
        self.rag = rag_pipeline
        self.miner = knowledge_miner
        self.meta = meta_learning
        self.tracker = topic_tracker
        self.interval = learning_interval_hours
        self.running = False
        self.learned_topics: List[str] = []
        self.new_skills_found: List[str] = []
        self.cycle_count: int = 0
        self._last_cycle_result: Optional[LearningEntry] = None

        self.learning_log_path = Path("./data/auto_learning.json")
        self._ensure_data_dir()
        self._load_log()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    async def start_continuous_learning(self):
        """Sürekli öğrenme döngüsünü başlat."""
        self.running = True
        logger.info("🎓 AutoLearningEngine started (interval=%dh)", self.interval)
        while self.running:
            try:
                await self._learning_cycle()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Learning cycle error: %s", exc)
            await asyncio.sleep(self.interval * 3600)
        logger.info("🎓 AutoLearningEngine stopped")

    def stop(self):
        """Öğrenmeyi durdur."""
        self.running = False

    async def run_single_cycle(self) -> LearningEntry:
        """Tek bir öğrenme döngüsü çalıştır (manuel/test için)."""
        return await self._learning_cycle()

    def get_status(self) -> Dict[str, Any]:
        """Mevcut durum özeti."""
        return {
            "running": self.running,
            "cycle_count": self.cycle_count,
            "learned_topics_count": len(self.learned_topics),
            "new_skills_found": self.new_skills_found,
            "interval_hours": self.interval,
            "last_cycle": self._last_cycle_result.to_dict()
            if self._last_cycle_result
            else None,
        }

    # ------------------------------------------------------------------ #
    #  Learning cycle
    # ------------------------------------------------------------------ #

    async def _learning_cycle(self) -> LearningEntry:
        """Bir öğrenme döngüsü."""
        logger.info("🎓 Auto-learning cycle #%d started", self.cycle_count + 1)
        cycle_start = datetime.now()

        # 1. Trend konuları belirle
        trends = await self._identify_trends()

        # 2. Kullanıcı ilgi alanlarına göre filtrele
        interests = await self._get_user_interests()
        topics = [
            t
            for t in trends
            if any(i.lower() in t.lower() for i in interests)
        ]

        # Eğer ilgi filtresi boşsa, trendlerin tamamını al
        if not topics:
            topics = trends[:5]

        # 3. Her konu için araştır
        researched: List[str] = []
        for topic in topics[:5]:  # Max 5 konu / döngü
            try:
                await self._research_topic(topic)
                researched.append(topic)
                self.learned_topics.append(topic)
            except Exception as exc:
                logger.warning("Research failed for '%s': %s", topic, exc)

        # 4. Yeni skill keşif
        discovered_skills: List[str] = []
        try:
            discovered_skills = await self._discover_new_skills()
            self.new_skills_found.extend(discovered_skills)
        except Exception as exc:
            logger.warning("Skill discovery failed: %s", exc)

        # 5. Performans optimizasyonu
        perf: Dict[str, Any] = {}
        try:
            perf = await self._optimize_performance()
        except Exception as exc:
            logger.warning("Performance optimization failed: %s", exc)

        # 6. Log kaydet
        entry = LearningEntry(
            timestamp=cycle_start.isoformat(),
            topics=researched,
            new_skills=discovered_skills,
            perf_metrics=perf,
            notes=f"Cycle #{self.cycle_count + 1}",
        )
        self._last_cycle_result = entry
        self.cycle_count += 1
        self._save_log()

        logger.info(
            "🎓 Auto-learning cycle completed (%d topics, %d skills)",
            len(researched),
            len(discovered_skills),
        )
        return entry

    # ------------------------------------------------------------------ #
    #  Trend identification
    # ------------------------------------------------------------------ #

    async def _identify_trends(self) -> List[str]:
        """Güncel trend konuları belirle."""
        trends: List[str] = []

        # Reddit hot posts (teknoloji)
        if self.search and hasattr(self.search, "get_reddit_hot"):
            try:
                posts = await self.search.get_reddit_hot("technology", limit=10)
                trends.extend([p.title for p in posts])
            except Exception:
                pass

        # Bilgi madenciliği — web araması ile trending başlıklar
        if self.miner:
            try:
                # Tekli arama: "trending technology 2025"
                news = await self.miner.web_search(
                    "trending technology 2025", max_results=5
                )
                trends.extend([n.get("title", "") for n in news])
            except Exception:
                pass

            # İkinci arama: "latest science breakthrough"
            try:
                science = await self.miner.web_search(
                    "latest science breakthrough", max_results=5
                )
                trends.extend([n.get("title", "") for n in science])
            except Exception:
                pass

        # Topic tracker’dan da trend skorlarını al
        if self.tracker and hasattr(self.tracker, "get_trending"):
            try:
                tracker_trends = self.tracker.get_trending(limit=10)
                trends.extend([t.topic for t in tracker_trends])
            except Exception:
                pass

        # Tekilleştir ve limitli dön
        unique = list(dict.fromkeys(t for t in trends if t))
        return unique[:20]

    # ------------------------------------------------------------------ #
    #  User interests
    # ------------------------------------------------------------------ #

    async def _get_user_interests(self) -> List[str]:
        """Kullanıcı ilgi alanlarını belirle."""
        interests: List[str] = []
        profile_path = Path("./data/user_profile.md")
        if profile_path.exists():
            text = profile_path.read_text().lower()
            if "teknoloji" in text:
                interests.append("technology")
            if "yapay zeka" in text or "ai" in text:
                interests.append("artificial intelligence")
            if "yazılım" in text or "software" in text:
                interests.append("software")
            if "bilim" in text or "science" in text:
                interests.append("science")
            if "sağlık" in text or "health" in text:
                interests.append("health")
            if "ekonomi" in text or "economy" in text:
                interests.append("economy")
        else:
            # Meta-learning’den çıkarım yap
            if self.meta and hasattr(self.meta, "get_user_interests"):
                try:
                    interests = self.meta.get_user_interests()
                except Exception:
                    pass

        return interests if interests else ["technology", "science", "programming"]

    # ------------------------------------------------------------------ #
    #  Deep research
    # ------------------------------------------------------------------ #

    async def _research_topic(self, topic: str):
        """Bir konu hakkında derinlemesine araştırma yap."""
        logger.info("🔬 Researching: %s", topic)

        # Multi-source search
        if self.search and hasattr(self.search, "search"):
            try:
                results = await self.search.search(topic, max_results=10)
                if self.rag and hasattr(self.rag, "add_document"):
                    for r in results:
                        snippet = getattr(r, "snippet", "")
                        title = getattr(r, "title", "")
                        url = getattr(r, "url", "")
                        source = getattr(r, "source", "")
                        await self.rag.add_document(
                            content=f"{title}\n{snippet}\n{url}",
                            metadata={
                                "source": source,
                                "topic": topic,
                                "learned_at": datetime.now().isoformat(),
                            },
                        )
            except Exception as exc:
                logger.debug("Search/RAG error for '%s': %s", topic, exc)

        # Akademik kaynaklar
        if self.miner and hasattr(self.miner, "search_arxiv"):
            try:
                papers = await self.miner.search_arxiv(topic, max_results=3)
                logger.info(
                    "📚 %d academic papers found for %s", len(papers), topic
                )
                # RAG’e akademik doküman ekle
                if self.rag:
                    for paper in papers:
                        title = paper.get("title", "")
                        summary = paper.get("summary", "")
                        await self.rag.add_document(
                            content=f"ARXIV: {title}\n{summary}",
                            metadata={
                                "source": "arxiv",
                                "topic": topic,
                                "type": "academic",
                            },
                        )
            except Exception as exc:
                logger.debug("Arxiv search error for '%s': %s", topic, exc)

    # ------------------------------------------------------------------ #
    #  New skill discovery
    # ------------------------------------------------------------------ #

    async def _discover_new_skills(self) -> List[str]:
        """GitHub / trend kaynaklarından yeni skill'leri keşfet."""
        logger.info("🔍 Discovering new skills...")
        discovered: List[str] = []

        # 1. GitHub trending repos
        if self.miner and hasattr(self.miner, "web_search"):
            try:
                trending = await self.miner.web_search(
                    "github trending repositories this week", max_results=5
                )
                for item in trending:
                    title = item.get("title", "")
                    if any(kw in title.lower() for kw in ("python", "rust", "go", "javascript")):
                        discovered.append(f"repo_skill:{title}")
            except Exception:
                pass

        # 2. unified_skill_manager ile entegrasyon
        skill_mgr_path = Path("./turkish_jarvis/skills/unified_skill_manager.py")
        if skill_mgr_path.exists():
            try:
                # Dinamik import — opsiyonel, hata durumunda sessiz
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "unified_skill_manager", str(skill_mgr_path)
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[arg-type]
                if hasattr(mod, "UnifiedSkillManager"):
                    mgr = mod.UnifiedSkillManager()
                    if hasattr(mgr, "discover_skills"):
                        skills = mgr.discover_skills()
                        discovered.extend(skills)
            except Exception:
                pass

        # 3. Meta-learning: hangi alanlarda yetersiz kalındı?
        if self.meta and hasattr(self.meta, "suggest_new_skills"):
            try:
                suggestions = self.meta.suggest_new_skills()
                discovered.extend(suggestions)
            except Exception:
                pass

        # Tekilleştir
        return list(dict.fromkeys(discovered))[:10]

    # ------------------------------------------------------------------ #
    #  Performance optimization
    # ------------------------------------------------------------------ #

    async def _optimize_performance(self) -> Dict[str, Any]:
        """Kendi performansını optimize et."""
        report: Dict[str, Any] = {}

        if self.meta:
            try:
                if hasattr(self.meta, "analyze_performance"):
                    raw_report = self.meta.analyze_performance(window=50)
                    report["meta_analysis"] = raw_report
                    logger.info("📊 Performance report: %s", raw_report)

                # Model seçimi optimizasyonu
                if hasattr(self.meta, "get_best_model_for_task"):
                    best_model = self.meta.get_best_model_for_task("general")
                    report["best_model"] = best_model

                # Prompt optimizasyonu
                if hasattr(self.meta, "optimize_prompts"):
                    prompt_delta = self.meta.optimize_prompts()
                    report["prompt_changes"] = prompt_delta

            except Exception as exc:
                logger.debug("Meta-learning optimization error: %s", exc)

        return report

    # ------------------------------------------------------------------ #
    #  Persistence
    # ------------------------------------------------------------------ #

    def _ensure_data_dir(self):
        """Veri dizinini oluştur."""
        self.learning_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_log(self):
        """Önceki öğrenme logunu yükle."""
        if self.learning_log_path.exists():
            try:
                data = json.loads(self.learning_log_path.read_text())
                self.learned_topics = data.get("learned_topics", [])
                self.cycle_count = data.get("total_cycles", 0)
                self.new_skills_found = data.get("new_skills_found", [])
            except Exception:
                pass

    def _save_log(self):
        """Öğrenme logunu kaydet."""
        self._ensure_data_dir()
        payload = {
            "last_run": datetime.now().isoformat(),
            "learned_topics": self.learned_topics[-100:],  # son 100
            "total_cycles": self.cycle_count,
            "new_skills_found": self.new_skills_found[-50:],
            "last_cycle": self._last_cycle_result.to_dict()
            if self._last_cycle_result
            else None,
        }
        self.learning_log_path.write_text(json.dumps(payload, indent=2))


# ------------------------------------------------------------------ #
#  LearningEntry helpers
# ------------------------------------------------------------------ #


def _learning_entry_to_dict(self) -> Dict[str, Any]:
    return {
        "timestamp": self.timestamp,
        "topics": self.topics,
        "new_skills": self.new_skills,
        "perf_metrics": self.perf_metrics,
        "notes": self.notes,
    }


LearningEntry.to_dict = _learning_entry_to_dict  # type: ignore[attr-defined]
