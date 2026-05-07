"""Tests for self_healing.py."""

import ast
import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from turkish_jarvis.autonomy.self_healing import (
    HealingEvent,
    HealingResult,
    SelfHealingEngine,
)


def test_healing_result_defaults():
    r = HealingResult()
    assert r.success is False
    assert r.fix_applied is False
    assert r.rolled_back is False
    assert r.new_code is None
    assert r.test_passed is False
    assert r.healing_time == 0.0
    assert r.confidence == 0.0


def test_healing_event_defaults():
    e = HealingEvent()
    assert e.module == ""
    assert e.function == ""
    assert e.fix_success is False
    assert e.rolled_back is False


def test_syntax_ok():
    llm = AsyncMock()
    engine = SelfHealingEngine(llm, project_dir=".")
    assert engine._syntax_ok("def foo():\n    return 1\n") is True
    assert engine._syntax_ok("def foo(:\n    return 1\n") is False


def test_hash():
    llm = AsyncMock()
    engine = SelfHealingEngine(llm, project_dir=".")
    h1 = engine._hash("hello")
    h2 = engine._hash("hello")
    h3 = engine._hash("world")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 16


def test_is_allowed_path():
    llm = AsyncMock()
    engine = SelfHealingEngine(llm, project_dir="/tmp/project")
    # İzin verilen yol
    allowed = Path("/tmp/project/turkish_jarvis/tools/registry.py")
    assert engine._is_allowed_path(allowed) is True
    # İzin dışı yol
    forbidden = Path("/tmp/project/other_module.py")
    assert engine._is_allowed_path(forbidden) is False
    # Proje dışı yol
    outside = Path("/etc/passwd")
    assert engine._is_allowed_path(outside) is False


def test_backup_and_rollback():
    llm = AsyncMock()
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        engine = SelfHealingEngine(llm, project_dir=str(project_dir))

        # Test dosyası oluştur
        test_file = project_dir / "turkish_jarvis" / "test_mod.py"
        test_file.parent.mkdir(parents=True)
        original_content = "# original\ndef foo():\n    return 1\n"
        test_file.write_text(original_content)

        backup = engine._backup_file(test_file)
        assert backup.exists()
        assert backup.read_text() == original_content

        # Dosyayı değiştir
        test_file.write_text("# changed\n")
        engine._rollback(test_file, backup)
        assert test_file.read_text() == original_content


def test_apply_fix():
    llm = AsyncMock()
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        engine = SelfHealingEngine(llm, project_dir=str(project_dir))

        test_file = project_dir / "turkish_jarvis" / "test_mod.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("# old")

        new_code = "def foo():\n    return 42\n"
        assert engine._apply_fix(test_file, new_code) is True
        assert test_file.read_text() == new_code

        bad_code = "def foo(:\n    return 42\n"
        assert engine._apply_fix(test_file, bad_code) is False


def test_extract_location_from_trace():
    llm = AsyncMock()
    engine = SelfHealingEngine(llm, project_dir=".")
    trace = (
        'Traceback (most recent call last):\n'
        '  File "/project/turkish_jarvis/tools/registry.py", line 88, in execute\n'
        '    return func(**arguments)\n'
        '  File "/project/turkish_jarvis/tools/builtin.py", line 42, in search_web\n'
        '    result = requests.get(url)\n'
        'AttributeError: module requests has no attribute get\n'
    )
    lineno, func_name = engine._extract_location_from_trace(trace)
    assert lineno == 42
    assert func_name == "search_web"


def test_extract_code_block():
    text = (
        'Some analysis\n'
        '```python\n'
        'def foo():\n'
        '    return 1\n'
        '```\n'
        'More text'
    )
    code = SelfHealingEngine._extract_code_block(text)
    assert code == "def foo():\n    return 1"


def test_generate_test_from_error():
    llm = AsyncMock()
    engine = SelfHealingEngine(llm, project_dir=".")
    test = engine._generate_test_from_error(
        ValueError("bad input"), {"query": "test"}
    )
    assert test["input"] == {"query": "test"}
    assert test["expected_not"] == "bad input"


async def test_run_test_success():
    llm = AsyncMock()
    engine = SelfHealingEngine(llm, project_dir=".")
    code = "def add(x, y):\n    return x + y\n"
    # Geçici bir fonksiyon oluşturacağız ama _run_test kendi içinde import ediyor
    # Bu yüzden dosya tabanlı test yapalım
    test_file = Path(tempfile.gettempdir()) / "_healing_dummy.py"
    test_file.write_text(code)
    # _run_test tool_func parametresi kullanmıyor aslında, dosyadan yüklüyor
    # Basit bir test: kodu doğrudan parse et ve çalıştır
    passed = await engine._run_test(
        tool_func=lambda: None,
        test_case={"input": {"x": 1, "y": 2}, "expected_not": "error"},
        file_path=test_file,
        new_code=code,
    )
    assert passed is True
    test_file.unlink(missing_ok=True)


async def test_reload_and_test_module():
    llm = AsyncMock()
    engine = SelfHealingEngine(llm, project_dir=".")
    code = "MODULE_VAR = 42\n"
    test_file = Path(tempfile.gettempdir()) / "_healing_mod_test.py"
    test_file.write_text(code)
    passed = await engine._reload_and_test_module(test_file, code)
    assert passed is True
    test_file.unlink(missing_ok=True)


def main():
    test_healing_result_defaults()
    test_healing_event_defaults()
    test_syntax_ok()
    test_hash()
    test_is_allowed_path()
    test_backup_and_rollback()
    test_apply_fix()
    test_extract_location_from_trace()
    test_extract_code_block()
    test_generate_test_from_error()

    asyncio.run(test_run_test_success())
    asyncio.run(test_reload_and_test_module())

    print("All tests passed!")


if __name__ == "__main__":
    main()
