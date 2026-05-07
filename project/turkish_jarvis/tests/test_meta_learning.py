"""Unit tests for meta_learning.py."""

import os
import sqlite3
import tempfile

from turkish_jarvis.autonomy.meta_learning import (
    ImprovementSuggestion,
    LearningStats,
    MetaLearningEngine,
    PerformanceReport,
)


def test_init_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "meta.db")
        engine = MetaLearningEngine(db_path=db_path)
        assert os.path.exists(db_path)
        # Verify tables exist
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {r[0] for r in cur.fetchall()}
            assert "interaction_log" in tables
            assert "prompt_versions" in tables
            assert "model_performance" in tables


def test_log_interaction():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MetaLearningEngine(db_path=os.path.join(tmpdir, "meta.db"))
        engine.log_interaction(
            session_id="sess-1",
            objective="2+2 nedir",
            tools_used=["calculator"],
            model="qwen3-coder:30b",
            prompt_version="v1",
            success=True,
            latency=120.0,
            user_rating=5,
            error=None,
            replan_count=0,
            message_count=4,
        )
        report = engine.analyze_performance(window=10)
        assert report.total_interactions == 1
        assert report.success_rate == 1.0
        assert report.avg_latency == 120.0
        assert report.best_model == "qwen3-coder:30b"


def test_suggest_improvements():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MetaLearningEngine(db_path=os.path.join(tmpdir, "meta.db"))
        # Seed data with a failing tool
        for i in range(10):
            engine.log_interaction(
                session_id=f"sess-{i}",
                objective="hesaplama",
                tools_used=["calculator"],
                model="mistral",
                prompt_version="v1",
                success=(i < 2),  # 20% success
                latency=200.0,
                error="Tool error" if i >= 2 else None,
            )
        suggestions = engine.suggest_improvements()
        assert any(s.category == "tool" for s in suggestions)


def test_optimize_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MetaLearningEngine(db_path=os.path.join(tmpdir, "meta.db"))
        base = "Sen TurkishJARVIS'sin."
        result = engine.optimize_prompt(base, metric="success_rate")
        assert result == base  # No alternatives yet

        # Simulate another prompt version performing better
        v2 = base + " Yardımcı ol."
        v2_id = engine._hash_prompt(v2)
        with engine._conn() as conn:
            conn.execute(
                "INSERT INTO prompt_versions (version_id, prompt_text, success_count, fail_count) VALUES (?, ?, ?, ?)",
                (v2_id, v2, 10, 0),
            )
            conn.commit()

        result2 = engine.optimize_prompt(base, metric="success_rate")
        assert result2 == v2


def test_select_best_model():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MetaLearningEngine(db_path=os.path.join(tmpdir, "meta.db"))
        # Seed model performance
        for i in range(5):
            engine.log_interaction(
                session_id=f"sess-{i}",
                objective="kod yaz",
                tools_used=[],
                model="qwen3-coder:30b",
                prompt_version="v1",
                success=True,
                latency=100.0,
            )
        selected = engine.select_best_model("coding")
        assert selected == "qwen3-coder:30b"


def test_get_learning_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MetaLearningEngine(db_path=os.path.join(tmpdir, "meta.db"))
        engine.log_interaction(
            session_id="s1",
            objective="selam",
            tools_used=[],
            model="gemma4",
            prompt_version="v1",
            success=True,
            latency=50.0,
        )
        stats = engine.get_learning_stats()
        assert stats.total_interactions == 1
        assert stats.unique_objectives == 1
        assert "gemma4" in stats.model_performance_matrix


def test_export_import_knowledge():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = MetaLearningEngine(db_path=os.path.join(tmpdir, "meta.db"))
        engine.log_interaction(
            session_id="s1",
            objective="test",
            tools_used=[],
            model="m1",
            prompt_version="v1",
            success=True,
            latency=10.0,
        )
        export_path = os.path.join(tmpdir, "knowledge.json")
        engine.export_knowledge(export_path)
        assert os.path.exists(export_path)

        engine2 = MetaLearningEngine(db_path=os.path.join(tmpdir, "meta2.db"))
        engine2.import_knowledge(export_path)
        stats = engine2.get_learning_stats()
        # Model performance matrix should be imported
        assert stats.model_performance_matrix


if __name__ == "__main__":
    test_init_db()
    test_log_interaction()
    test_suggest_improvements()
    test_optimize_prompt()
    test_select_best_model()
    test_get_learning_stats()
    test_export_import_knowledge()
    print("All meta_learning tests passed.")
