"""Meta-öğrenme — başarı/başarısızlık izleme, strateji optimizasyonu, prompt tuning."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PerformanceReport:
    total_interactions: int = 0
    success_rate: float = 0.0
    avg_latency: float = 0.0
    best_model: str = ""
    worst_tool: str = ""
    top_errors: list[str] = field(default_factory=list)
    trends: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImprovementSuggestion:
    category: str = "model"  # "model" | "tool" | "prompt" | "plan"
    description: str = ""
    confidence: float = 0.0
    expected_impact: float = 0.0
    data_evidence: str = ""


@dataclass
class LearningStats:
    total_interactions: int = 0
    unique_objectives: int = 0
    skills_learned: int = 0
    self_healing_count: int = 0
    prompt_versions_tested: int = 0
    current_best_prompt_version: str = ""
    model_performance_matrix: dict[str, dict] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class MetaLearningEngine:
    """Asistanın kendi performansını ölçmesi, analiz etmesi ve iyileştirmesi."""

    def __init__(self, db_path: str = "./data/meta_learning.db") -> None:
        self.db_path = db_path
        # Ensure parent directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS interaction_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            objective TEXT,
            tools_used TEXT,  -- JSON array
            model TEXT,
            prompt_version TEXT,
            success BOOLEAN,
            latency_ms REAL,
            user_rating INTEGER,
            error TEXT,
            replan_count INTEGER,
            message_count INTEGER
        );

        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id TEXT UNIQUE,
            prompt_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            avg_latency REAL
        );

        CREATE TABLE IF NOT EXISTS model_performance (
            model TEXT,
            task_type TEXT,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            avg_latency REAL,
            PRIMARY KEY (model, task_type)
        );

        CREATE INDEX IF NOT EXISTS idx_interaction_timestamp
            ON interaction_log(timestamp);

        CREATE INDEX IF NOT EXISTS idx_interaction_session
            ON interaction_log(session_id);
        """
        with self._conn() as conn:
            conn.executescript(sql)
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_interaction(
        self,
        session_id: str,
        objective: str,
        tools_used: list[str],
        model: str,
        prompt_version: str,
        success: bool,
        latency: float,
        user_rating: int | None = None,
        error: str | None = None,
        replan_count: int = 0,
        message_count: int = 0,
    ) -> None:
        """Her etkileşimi kaydet."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO interaction_log
                (session_id, objective, tools_used, model, prompt_version,
                 success, latency_ms, user_rating, error, replan_count, message_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    objective,
                    json.dumps(tools_used, ensure_ascii=False),
                    model,
                    prompt_version,
                    success,
                    latency,
                    user_rating,
                    error,
                    replan_count,
                    message_count,
                ),
            )
            conn.commit()

        # Update prompt_versions counters
        self._update_prompt_stats(prompt_version, success, latency)

        # Derive task_type from objective (simple heuristic)
        task_type = self._guess_task_type(objective)
        self._update_model_stats(model, task_type, success, latency)

        logger.info(
            "📊 Meta-learning logged: session=%s model=%s success=%s latency=%.1fms",
            session_id,
            model,
            success,
            latency,
        )

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze_performance(self, window: int = 100) -> PerformanceReport:
        """Son N etkileşimin analizi."""
        with self._conn() as conn:
            cur = conn.execute(
                """
                SELECT success, latency_ms, model, tools_used, error, timestamp
                FROM interaction_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (window,),
            )
            rows = cur.fetchall()

        if not rows:
            return PerformanceReport()

        total = len(rows)
        successes = sum(1 for r in rows if r[0])
        latencies = [r[1] for r in rows if r[1] is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        # Best model
        model_stats: dict[str, dict] = {}
        tool_fails: dict[str, int] = {}
        error_counts: dict[str, int] = {}
        for success_flag, latency_val, model, tools_raw, error, _ in rows:
            model_stats.setdefault(model, {"success": 0, "fail": 0, "latency": []})
            if success_flag:
                model_stats[model]["success"] += 1
            else:
                model_stats[model]["fail"] += 1
            if latency_val is not None:
                model_stats[model]["latency"].append(latency_val)

            if not success_flag and tools_raw:
                try:
                    tools = json.loads(tools_raw)
                    for t in tools:
                        tool_fails[t] = tool_fails.get(t, 0) + 1
                except json.JSONDecodeError:
                    pass

            if error:
                err_key = error[:100]
                error_counts[err_key] = error_counts.get(err_key, 0) + 1

        best_model = ""
        best_rate = -1.0
        for m, stats in model_stats.items():
            total_m = stats["success"] + stats["fail"]
            if total_m == 0:
                continue
            rate = stats["success"] / total_m
            if rate > best_rate:
                best_rate = rate
                best_model = m

        worst_tool = ""
        worst_count = -1
        for t, c in tool_fails.items():
            if c > worst_count:
                worst_count = c
                worst_tool = t

        top_errors = sorted(error_counts, key=lambda k: error_counts[k], reverse=True)[:5]

        # Trends: split rows into first/second half
        half = total // 2
        if half > 0:
            first_success = sum(1 for r in rows[:half] if r[0])
            second_success = sum(1 for r in rows[half:] if r[0])
            first_rate = first_success / half
            second_rate = second_success / (total - half) if (total - half) else 0
            trends = {
                "success_rate_first_half": first_rate,
                "success_rate_second_half": second_rate,
                "improving": second_rate > first_rate,
            }
        else:
            trends = {}

        return PerformanceReport(
            total_interactions=total,
            success_rate=successes / total if total else 0.0,
            avg_latency=avg_latency,
            best_model=best_model,
            worst_tool=worst_tool,
            top_errors=top_errors,
            trends=trends,
        )

    def suggest_improvements(self) -> list[ImprovementSuggestion]:
        """Veriye dayalı iyileştirme önerileri."""
        suggestions: list[ImprovementSuggestion] = []
        report = self.analyze_performance(window=100)

        # 1. Model suggestions
        with self._conn() as conn:
            cur = conn.execute(
                """
                SELECT model,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as s,
                       SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as f,
                       AVG(latency_ms) as lat
                FROM interaction_log
                GROUP BY model
                HAVING (s + f) > 5
                """
            )
            model_rows = cur.fetchall()

        if len(model_rows) >= 2:
            model_rows_sorted = sorted(
                model_rows,
                key=lambda r: (r[1] / (r[1] + r[2]) if (r[1] + r[2]) else 0),
                reverse=True,
            )
            best = model_rows_sorted[0]
            worst = model_rows_sorted[-1]
            best_rate = best[1] / (best[1] + best[2]) if (best[1] + best[2]) else 0
            worst_rate = worst[1] / (worst[1] + worst[2]) if (worst[1] + worst[2]) else 0
            if best[3] and worst[3] and best[3] < worst[3]:
                delta = (worst[3] - best[3]) / worst[3] * 100
                suggestions.append(
                    ImprovementSuggestion(
                        category="model",
                        description=(
                            f"'{best[0]}' ile %{delta:.0f} daha hızlı "
                            f"ama %{abs(best_rate - worst_rate) * 100:.0f} "
                            f"daha {'yüksek' if best_rate > worst_rate else 'düşük'} başarı oranı var."
                        ),
                        confidence=0.75,
                        expected_impact=0.15,
                        data_evidence=f"{best[1] + best[2]} deneme",
                    )
                )

        # 2. Tool suggestions
        with self._conn() as conn:
            cur = conn.execute(
                """
                SELECT tools_used, success
                FROM interaction_log
                WHERE tools_used IS NOT NULL AND tools_used != '[]'
                ORDER BY id DESC
                LIMIT 200
                """
            )
            tool_rows = cur.fetchall()

        tool_stats: dict[str, dict] = {}
        for tools_raw, success_flag in tool_rows:
            try:
                tools = json.loads(tools_raw)
                for t in tools:
                    tool_stats.setdefault(t, {"success": 0, "fail": 0})
                    if success_flag:
                        tool_stats[t]["success"] += 1
                    else:
                        tool_stats[t]["fail"] += 1
            except json.JSONDecodeError:
                continue

        for tool, stats in tool_stats.items():
            total = stats["success"] + stats["fail"]
            if total >= 5:
                fail_rate = stats["fail"] / total
                if fail_rate > 0.15:
                    suggestions.append(
                        ImprovementSuggestion(
                            category="tool",
                            description=(
                                f"'{tool}' aracı %{fail_rate * 100:.0f} başarısız. "
                                f"Prompt veya parametre düzeltmesi önerilir."
                            ),
                            confidence=min(0.9, fail_rate + 0.3),
                            expected_impact=fail_rate * 0.5,
                            data_evidence=f"{total} kullanım, {stats['fail']} başarısız",
                        )
                    )

        # 3. Prompt suggestions
        with self._conn() as conn:
            cur = conn.execute(
                """
                SELECT version_id, success_count, fail_count, avg_latency
                FROM prompt_versions
                WHERE (success_count + fail_count) > 5
                ORDER BY (success_count * 1.0 / (success_count + fail_count)) DESC
                """
            )
            pv_rows = cur.fetchall()

        if len(pv_rows) >= 2:
            best_pv = pv_rows[0]
            worst_pv = pv_rows[-1]
            best_pv_rate = best_pv[1] / (best_pv[1] + best_pv[2])
            worst_pv_rate = worst_pv[1] / (worst_pv[1] + worst_pv[2])
            if best_pv_rate - worst_pv_rate > 0.05:
                suggestions.append(
                    ImprovementSuggestion(
                        category="prompt",
                        description=(
                            f"'{best_pv[0]}' prompt versiyonu "
                            f"'{worst_pv[0]}'den %{(best_pv_rate - worst_pv_rate) * 100:.0f} "
                            f"daha başarılı. Prompt optimizasyonu uygulanmalı."
                        ),
                        confidence=abs(best_pv_rate - worst_pv_rate),
                        expected_impact=abs(best_pv_rate - worst_pv_rate) * 0.8,
                        data_evidence=f"{best_pv[1] + best_pv[2]} test",
                    )
                )

        # 4. Plan suggestion (replan count)
        with self._conn() as conn:
            cur = conn.execute(
                """
                SELECT AVG(replan_count) as avg_replan
                FROM interaction_log
                WHERE replan_count > 0
                """
            )
            row = cur.fetchone()
            avg_replan = row[0] or 0.0

        if avg_replan > 1.5:
            suggestions.append(
                ImprovementSuggestion(
                    category="plan",
                    description=(
                        f"Ortalama replan sayısı {avg_replan:.1f}. "
                        f"Planlama stratejisi gözden geçirilmeli."
                    ),
                    confidence=min(0.85, avg_replan / 5.0),
                    expected_impact=0.2,
                    data_evidence=f"Ortalama replan: {avg_replan:.1f}",
                )
            )

        return suggestions

    def optimize_prompt(self, base_prompt: str, metric: str = "success_rate") -> str:
        """Prompt varyasyonlarını test et, en iyisini seç.

        Şu an basit A/B mantığı: mevcut prompt'un versiyonunu kaydeder,
        veritabanındaki mevcut versiyonları karşılaştırır, en iyi olanı
        döndürür. Yeni varyasyonlar yoksa base_prompt'u döndürür.
        """
        version_id = self._hash_prompt(base_prompt)

        # Register current prompt if not exists
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT 1 FROM prompt_versions WHERE version_id = ?", (version_id,)
            )
            if cur.fetchone() is None:
                conn.execute(
                    "INSERT INTO prompt_versions (version_id, prompt_text) VALUES (?, ?)",
                    (version_id, base_prompt),
                )
                conn.commit()

        # Pick best existing prompt version by metric
        with self._conn() as conn:
            if metric == "success_rate":
                cur = conn.execute(
                    """
                    SELECT version_id, prompt_text,
                           (success_count * 1.0 / NULLIF(success_count + fail_count, 0)) as rate
                    FROM prompt_versions
                    WHERE (success_count + fail_count) > 0
                    ORDER BY rate DESC
                    LIMIT 1
                    """
                )
            elif metric == "latency":
                cur = conn.execute(
                    """
                    SELECT version_id, prompt_text, avg_latency
                    FROM prompt_versions
                    WHERE avg_latency IS NOT NULL
                    ORDER BY avg_latency ASC
                    LIMIT 1
                    """
                )
            else:
                cur = conn.execute(
                    """
                    SELECT version_id, prompt_text,
                           (success_count * 1.0 / NULLIF(success_count + fail_count, 0)) as rate
                    FROM prompt_versions
                    WHERE (success_count + fail_count) > 0
                    ORDER BY rate DESC
                    LIMIT 1
                    """
                )
            row = cur.fetchone()

        if row:
            best_version, best_prompt, _ = row
            if best_version != version_id:
                logger.info(
                    "🎯 Prompt optimize edildi: %s -> %s (metric=%s)",
                    version_id[:8],
                    best_version[:8],
                    metric,
                )
            return best_prompt

        return base_prompt

    def select_best_model(self, task_type: str, history: list[dict] | None = None) -> str:
        """Görev tipine göre en iyi modeli seç (öğrenilmiş)."""
        with self._conn() as conn:
            cur = conn.execute(
                """
                SELECT model,
                       success_count,
                       fail_count,
                       avg_latency
                FROM model_performance
                WHERE task_type = ?
                ORDER BY (success_count * 1.0 / NULLIF(success_count + fail_count, 0)) DESC,
                         avg_latency ASC
                LIMIT 1
                """,
                (task_type,),
            )
            row = cur.fetchone()

        if row:
            model, success_count, fail_count, latency = row
            total = success_count + fail_count
            rate = success_count / total if total else 0
            logger.info(
                "🧠 Model seçildi: %s (task=%s, rate=%.2f, latency=%.1fms)",
                model,
                task_type,
                rate,
                latency or 0,
            )
            return model

        # Fallback: use global best model from recent interactions
        report = self.analyze_performance(window=50)
        if report.best_model:
            return report.best_model

        # Ultimate fallback
        return os.getenv("JARVIS_OLLAMA_MODEL", "qwen3-coder:30b")

    def get_learning_stats(self) -> LearningStats:
        """Öğrenme istatistiklerini döndür."""
        with self._conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM interaction_log"
            ).fetchone()[0]

            unique_obj = conn.execute(
                "SELECT COUNT(DISTINCT objective) FROM interaction_log"
            ).fetchone()[0]

            pv_tested = conn.execute(
                "SELECT COUNT(*) FROM prompt_versions"
            ).fetchone()[0]

            best_pv = conn.execute(
                """
                SELECT version_id
                FROM prompt_versions
                ORDER BY (success_count * 1.0 / NULLIF(success_count + fail_count, 0)) DESC
                LIMIT 1
                """
            ).fetchone()
            best_pv_id = best_pv[0] if best_pv else ""

            cur = conn.execute(
                "SELECT model, task_type, success_count, fail_count FROM model_performance"
            )
            mp_rows = cur.fetchall()

        matrix: dict[str, dict] = {}
        for model, task_type, success_count, fail_count in mp_rows:
            matrix.setdefault(model, {})[task_type] = {
                "success_rate": success_count / (success_count + fail_count)
                if (success_count + fail_count)
                else 0,
                "success_count": success_count,
                "fail_count": fail_count,
            }

        # self_healing_count and skills_learned are not tracked in DB by this module;
        # they are expected to be injected via update_learning_stats() or kept in memory.
        return LearningStats(
            total_interactions=total,
            unique_objectives=unique_obj,
            skills_learned=getattr(self, "_skills_learned", 0),
            self_healing_count=getattr(self, "_self_healing_count", 0),
            prompt_versions_tested=pv_tested,
            current_best_prompt_version=best_pv_id,
            model_performance_matrix=matrix,
        )

    def update_learning_stats(
        self, skills_learned: int | None = None, self_healing_count: int | None = None
    ) -> None:
        """Diğer modüllerden (AutoSkill, SelfHealing) gelen sayıları güncelle."""
        if skills_learned is not None:
            self._skills_learned = skills_learned
        if self_healing_count is not None:
            self._self_healing_count = self_healing_count

    def export_knowledge(self, file_path: str) -> None:
        """Öğrenilen bilgileri JSON olarak dışa aktar."""
        stats = self.get_learning_stats()
        suggestions = self.suggest_improvements()
        report = self.analyze_performance(window=1000)

        export_data = {
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stats": {
                "total_interactions": stats.total_interactions,
                "unique_objectives": stats.unique_objectives,
                "skills_learned": stats.skills_learned,
                "self_healing_count": stats.self_healing_count,
                "prompt_versions_tested": stats.prompt_versions_tested,
                "current_best_prompt_version": stats.current_best_prompt_version,
            },
            "model_performance_matrix": stats.model_performance_matrix,
            "latest_performance_report": {
                "total_interactions": report.total_interactions,
                "success_rate": report.success_rate,
                "avg_latency": report.avg_latency,
                "best_model": report.best_model,
                "worst_tool": report.worst_tool,
                "top_errors": report.top_errors,
                "trends": report.trends,
            },
            "suggestions": [
                {
                    "category": s.category,
                    "description": s.description,
                    "confidence": s.confidence,
                    "expected_impact": s.expected_impact,
                    "data_evidence": s.data_evidence,
                }
                for s in suggestions
            ],
        }

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        logger.info("📤 Knowledge exported to %s", file_path)

    def import_knowledge(self, file_path: str) -> None:
        """Önceden öğrenilen bilgileri içe aktar."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matrix = data.get("model_performance_matrix", {})
        with self._conn() as conn:
            for model, tasks in matrix.items():
                for task_type, metrics in tasks.items():
                    conn.execute(
                        """
                        INSERT INTO model_performance (model, task_type, success_count, fail_count)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(model, task_type)
                        DO UPDATE SET
                            success_count = success_count + excluded.success_count,
                            fail_count = fail_count + excluded.fail_count
                        """,
                        (
                            model,
                            task_type,
                            metrics.get("success_count", 0),
                            metrics.get("fail_count", 0),
                        ),
                    )
            conn.commit()

        stats = data.get("stats", {})
        self._skills_learned = stats.get("skills_learned", 0)
        self._self_healing_count = stats.get("self_healing_count", 0)

        logger.info("📥 Knowledge imported from %s", file_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_prompt_stats(
        self, version_id: str, success: bool, latency: float
    ) -> None:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT success_count, fail_count, avg_latency FROM prompt_versions WHERE version_id = ?",
                (version_id,),
            )
            row = cur.fetchone()
            if row is None:
                # We might not have the text here, but we can still track counters
                conn.execute(
                    """
                    INSERT INTO prompt_versions (version_id, prompt_text, success_count, fail_count, avg_latency)
                    VALUES (?, '', ?, ?, ?)
                    ON CONFLICT(version_id) DO UPDATE SET
                        success_count = success_count + ?,
                        fail_count = fail_count + ?,
                        avg_latency = ((avg_latency * (success_count + fail_count)) + ?) / (success_count + fail_count + 1)
                    """,
                    (
                        version_id,
                        1 if success else 0,
                        0 if success else 1,
                        latency,
                        1 if success else 0,
                        0 if success else 1,
                        latency,
                    ),
                )
            else:
                s_count, f_count, avg_lat = row
                total = s_count + f_count + 1
                new_avg = ((avg_lat or 0) * (s_count + f_count) + latency) / total
                if success:
                    conn.execute(
                        "UPDATE prompt_versions SET success_count = success_count + 1, avg_latency = ? WHERE version_id = ?",
                        (new_avg, version_id),
                    )
                else:
                    conn.execute(
                        "UPDATE prompt_versions SET fail_count = fail_count + 1, avg_latency = ? WHERE version_id = ?",
                        (new_avg, version_id),
                    )
            conn.commit()

    def _update_model_stats(
        self, model: str, task_type: str, success: bool, latency: float
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO model_performance (model, task_type, success_count, fail_count, avg_latency)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(model, task_type)
                DO UPDATE SET
                    success_count = success_count + ?,
                    fail_count = fail_count + ?,
                    avg_latency = ((avg_latency * (success_count + fail_count)) + ?) / (success_count + fail_count + 1)
                """,
                (
                    model,
                    task_type,
                    1 if success else 0,
                    0 if success else 1,
                    latency,
                    1 if success else 0,
                    0 if success else 1,
                    latency,
                ),
            )
            conn.commit()

    @staticmethod
    def _guess_task_type(objective: str) -> str:
        """Basit bir görev tipi tahmini."""
        obj_lower = objective.lower()
        if any(k in obj_lower for k in ("kod", "code", "script", "program", "python", "js", "java")):
            return "coding"
        if any(k in obj_lower for k in ("ara", "search", "bul", "find", "google", "web")):
            return "search"
        if any(k in obj_lower for k in ("hesap", "calc", "math", "sayı", "topla", "çarp")):
            return "math"
        if any(k in obj_lower for k in ("ev", "home", "ışık", "light", "klima", "thermostat")):
            return "home_automation"
        if any(k in obj_lower for k in ("çeviri", "translate", "tercüme", "dil")):
            return "translation"
        if any(k in obj_lower for k in ("chat", "konuş", "sohbet", "selam", "nasıl")):
            return "quick_chat"
        return "general"

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        import hashlib

        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
