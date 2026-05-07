"""Built-in tools for the TurkishJARVIS agent."""

import ast
import math
import operator
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import aiohttp


async def get_current_time() -> str:
    """Return the current local date and time as an ISO string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


async def get_weather(location: str) -> str:
    """Fetch current weather for a location using the Open-Meteo API.

    Args:
        location: City name (e.g., 'Istanbul', 'Ankara').

    Returns:
        A concise weather summary string.
    """
    # Simple geocoding via Open-Meteo
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    async with aiohttp.ClientSession() as session:
        async with session.get(geo_url, params={"name": location, "count": "1"}) as resp:
            if resp.status != 200:
                return f"Hava durumu alınamadı (HTTP {resp.status})."
            geo = await resp.json()
            results = geo.get("results", [])
            if not results:
                return f"'{location}' için konum bulunamadı."
            lat = results[0]["latitude"]
            lon = results[0]["longitude"]
        weather_url = "https://api.open-meteo.com/v1/forecast"
        async with session.get(
            weather_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
            },
        ) as resp:
            if resp.status != 200:
                return f"Hava durumu alınamadı (HTTP {resp.status})."
            data = await resp.json()
    current = data.get("current_weather", {})
    temp = current.get("temperature", "?")
    wind = current.get("windspeed", "?")
    return (
        f"{location}: Sıcaklık {temp}°C, Rüzgar hızı {wind} km/s."
    )


async def calculator(expression: str) -> float:
    """Evaluate a safe mathematical expression.

    Only basic arithmetic and math functions are permitted.

    Args:
        expression: A math expression such as '2 + sqrt(16)'.

    Returns:
        The evaluated numeric result.

    Raises:
        ValueError: If the expression contains disallowed syntax.
    """
    allowed_nodes = {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Num,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Tuple,
        ast.List,
    }

    def _eval(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Constants must be numeric.")
        if isinstance(node, ast.Num):  # pragma: no cover
            return node.n
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return operator.add(left, right)
            if isinstance(node.op, ast.Sub):
                return operator.sub(left, right)
            if isinstance(node.op, ast.Mult):
                return operator.mul(left, right)
            if isinstance(node.op, ast.Div):
                return operator.truediv(left, right)
            if isinstance(node.op, ast.Pow):
                return operator.pow(left, right)
            if isinstance(node.op, ast.Mod):
                return operator.mod(left, right)
            raise ValueError("Unsupported binary operator.")
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError("Unsupported unary operator.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function names are allowed.")
            func_name = node.func.id
            if func_name not in SAFE_MATH:
                raise ValueError(f"Function '{func_name}' is not allowed.")
            args = [_eval(arg) for arg in node.args]
            return SAFE_MATH[func_name](*args)
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    SAFE_MATH: dict[str, Any] = {
        "abs": abs,
        "round": round,
        "max": max,
        "min": min,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": math.factorial,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Invalid expression syntax.") from exc

    for node in ast.walk(tree):
        if type(node) not in allowed_nodes:
            raise ValueError(
                f"Disallowed syntax: {type(node).__name__}"
            )

    return _eval(tree)


async def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the web using DuckDuckGo API via duckduckgo-search library.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of result dictionaries with 'title', 'href', and 'snippet'.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return [{"error": "duckduckgo-search library not installed."}]

    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            return results
    except Exception as exc:
        return [{"error": f"Search failed: {exc}"}]


async def read_file(path: str, max_lines: int = 100) -> str:
    """Read a text file up to a line limit.

    Args:
        path: File path to read.
        max_lines: Maximum number of lines to return.

    Returns:
        File content string.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with p.open("r", encoding="utf-8", errors="ignore") as fh:
        lines = []
        for _ in range(max_lines):
            line = fh.readline()
            if not line:
                break
            lines.append(line.rstrip("\n"))
    return "\n".join(lines)


async def write_file(path: str, content: str) -> bool:
    """Write text content to a file.

    Args:
        path: Destination file path.
        content: Text content to write.

    Returns:
        True on success.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        fh.write(content)
    return True


async def run_python(code: str) -> str:
    """Execute Python code in a sandboxed subprocess.

    Args:
        code: Python source code to execute.

    Returns:
        stdout + stderr combined output.
    """
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(code)
        tmp_path = fh.name

    try:
        proc = subprocess.run(
            ["python", "-u", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = proc.stdout
        if proc.stderr:
            output += "\n--- STDERR ---\n" + proc.stderr
        if proc.returncode != 0:
            output += f"\n--- RETURN CODE: {proc.returncode} ---"
        return output
    except subprocess.TimeoutExpired:
        return "Execution timed out after 30 seconds."
    except Exception as exc:
        return f"Execution error: {exc}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def system_info() -> dict[str, Any]:
    """Return basic system resource information.

    Returns:
        Dictionary with platform, cpu_count, ram_mb, disk_free_mb.
    """
    import psutil

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "ram_mb": round(mem.total / (1024 * 1024)),
        "ram_available_mb": round(mem.available / (1024 * 1024)),
        "disk_free_mb": round(disk.free / (1024 * 1024)),
    }


def register_all(registry: Any) -> None:
    """Register all built-in tools."""
    from turkish_jarvis.tools.registry import ToolRegistry

    if not isinstance(registry, ToolRegistry):
        raise TypeError("Expected ToolRegistry instance")

    registry.register(
        "get_current_time",
        get_current_time,
        {
            "description": "Get current date and time",
            "parameters": {"type": "object", "properties": {}},
        },
    )
    registry.register(
        "get_weather",
        get_weather,
        {
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name",
                    }
                },
                "required": ["location"],
            },
        },
    )
    registry.register(
        "calculator",
        calculator,
        {
            "description": "Evaluate a safe mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression such as '2 + sqrt(16)'",
                    }
                },
                "required": ["expression"],
            },
        },
    )
    registry.register(
        "web_search",
        web_search,
        {
            "description": "Search the web using DuckDuckGo",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                    },
                },
                "required": ["query"],
            },
        },
    )
    registry.register(
        "read_file",
        read_file,
        {
            "description": "Read a text file up to a line limit",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum lines to return",
                    },
                },
                "required": ["path"],
            },
        },
    )
    registry.register(
        "write_file",
        write_file,
        {
            "description": "Write text content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Destination file path",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to write",
                    },
                },
                "required": ["path", "content"],
            },
        },
    )
    registry.register(
        "run_python",
        run_python,
        {
            "description": "Execute Python code in a sandboxed subprocess",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python source code to execute",
                    }
                },
                "required": ["code"],
            },
        },
    )
    registry.register(
        "system_info",
        system_info,
        {
            "description": "Return basic system resource information",
            "parameters": {"type": "object", "properties": {}},
        },
    )
