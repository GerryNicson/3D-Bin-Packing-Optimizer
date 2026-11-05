from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
FORBIDDEN = (
    "requests", "urllib.request", "http.client", "httpx",
    "aiohttp", "socket", "anthropic", "openai",
)


def _is_forbidden(name: str) -> bool:
    """Return True if a module name is forbidden or inside a forbidden one."""
    return any(name == f or name.startswith(f + ".") for f in FORBIDDEN)


def _bad_imports(path: Path) -> list[str]:
    """List the forbidden modules imported by one source file."""
    found: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module] + [node.module + "." + a.name for a in node.names]
        else:
            continue
        found += [n for n in names if _is_forbidden(n)]
    return found


def test_no_network_imports():
    """No .py file under src/ imports a network or AI library."""
    files = sorted(SRC.rglob("*.py"))
    assert files, "no .py files found under src/"
    problems = {str(p.relative_to(SRC)): _bad_imports(p) for p in files}
    problems = {name: bad for name, bad in problems.items() if bad}
    assert not problems, "forbidden imports: %s" % problems
