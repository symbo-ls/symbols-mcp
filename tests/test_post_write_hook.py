"""The post-write hook template (templates/agent-rules/.claude/hooks/symbols-mcp-audit.sh).

Its size cap must count only the Symbols source folder named by symbols.json
`dir` (dot-folders pruned), and the heavy frank-audit pass must audit that
folder, not the repo root. A fake `npx` on PATH records how it is called.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = Path(os.environ.get(
    "SYMBOLS_MCP_HOOK_UNDER_TEST",
    ROOT / "templates" / "agent-rules" / ".claude" / "hooks" / "symbols-mcp-audit.sh",
))

pytestmark = pytest.mark.skipif(
    not (shutil.which("bash") and shutil.which("jq") and shutil.which("perl")),
    reason="hook needs bash, jq and perl",
)

COMPONENT = "export const Card = {\n  extends: 'Flex',\n  padding: 'A'\n}\n"


def _fake_npx(bin_dir: Path, log: Path) -> None:
    bin_dir.mkdir()
    npx = bin_dir / "npx"
    npx.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s\\n' \"$*\" >> '{log}'\n"
        "exit 0\n"
    )
    npx.chmod(0o755)


def _bulk(folder: Path, n: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (folder / f"f{i}.js").write_text("export default 1\n")


def _run(tmp_path: Path, project: Path, edited: Path, max_files: int = 20):
    log = tmp_path / "npx.log"
    bin_dir = tmp_path / "bin"
    _fake_npx(bin_dir, log)
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["SYMBOLS_MCP_AUDIT_MAX_FILES"] = str(max_files)
    env["TMPDIR"] = str(tmp_path)
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(edited)}})
    proc = subprocess.run(
        ["bash", str(HOOK)], input=payload, capture_output=True, text=True,
        env=env, cwd=project, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    calls = log.read_text().splitlines() if log.exists() else []
    return calls


def _project(tmp_path: Path, conf: dict, src: str = "symbols") -> tuple[Path, Path]:
    project = tmp_path / "proj"
    comp = project / src / "components"
    comp.mkdir(parents=True)
    edited = comp / "Card.js"
    edited.write_text(COMPONENT)
    (project / "symbols.json").write_text(json.dumps(conf))
    return project, edited


def test_counts_only_the_dir_and_skips_dot_folders(tmp_path):
    project, edited = _project(tmp_path, {"key": "acme", "dir": "./symbols"})
    # Far more .js outside the Symbols folder than the cap — none of it counts.
    _bulk(project / "tools", 60)
    _bulk(project / ".claude" / "worktrees" / "a", 60)
    _bulk(project / "symbols" / ".cache", 60)
    calls = _run(tmp_path, project, edited)
    assert len(calls) == 1, calls
    assert "@symbo.ls/frank-audit audit" in calls[0]
    assert calls[0].split(" audit ", 1)[1].split()[0] == str(project / "symbols")


def test_dir_without_dot_slash_and_custom_name(tmp_path):
    project, edited = _project(tmp_path, {"key": "acme", "dir": "src"}, src="src")
    _bulk(project / "scripts", 60)
    calls = _run(tmp_path, project, edited)
    assert len(calls) == 1, calls
    assert calls[0].split(" audit ", 1)[1].split()[0] == str(project / "src")


def test_cap_still_applies_inside_the_dir(tmp_path):
    project, edited = _project(tmp_path, {"key": "acme", "dir": "./symbols"})
    _bulk(project / "symbols" / "functions", 60)
    assert _run(tmp_path, project, edited) == []


def test_mjs_counts_toward_the_cap(tmp_path):
    project, edited = _project(tmp_path, {"key": "acme", "dir": "./symbols"})
    folder = project / "symbols" / "functions"
    folder.mkdir(parents=True)
    for i in range(60):
        (folder / f"f{i}.mjs").write_text("export default 1\n")
    assert _run(tmp_path, project, edited) == []


def test_no_dir_falls_back_to_symbols_folder(tmp_path):
    project, edited = _project(tmp_path, {"key": "acme"})
    _bulk(project / "tools", 60)
    calls = _run(tmp_path, project, edited)
    assert len(calls) == 1, calls
    assert calls[0].split(" audit ", 1)[1].split()[0] == str(project / "symbols")


def test_file_outside_the_dir_skips_the_heavy_pass(tmp_path):
    project, _ = _project(tmp_path, {"key": "acme", "dir": "./symbols"})
    other = project / "tools" / "build.js"
    other.parent.mkdir()
    other.write_text("export default 1\n")
    assert _run(tmp_path, project, other) == []


def _hook_output(tmp_path: Path, project: Path, edited: Path) -> str:
    bin_dir = tmp_path / "bin2"
    _fake_npx(bin_dir, tmp_path / "npx2.log")
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["TMPDIR"] = str(tmp_path)
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(edited)}})
    proc = subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True,
                          text=True, env=env, cwd=project, timeout=60)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _component(name: str, keys: list[str]) -> str:
    body = "".join(f"  {k}: {{ text: '{k}' }},\n" for k in keys)
    return f"export const {name} = {{\n  extends: 'Flex',\n{body}}}\n"


def test_duplicate_scan_runs_in_the_dir_without_false_hits(tmp_path):
    project, edited = _project(tmp_path, {"key": "acme", "dir": "./symbols"})
    comp = project / "symbols" / "components"
    edited.write_text(_component("Card", ["Title", "Body", "Footer", "Badge", "Icon"]))
    (comp / "Tile.js").write_text(_component("Tile", ["Title", "Body", "Footer", "Badge"]))
    (comp / "Other.js").write_text(_component("Other", ["Media", "Caption", "Link", "Meta"]))
    out = _hook_output(tmp_path, project, edited)
    assert "Card shares 4 top-level keys with Tile" in out, out
    assert "Other" not in out, out
