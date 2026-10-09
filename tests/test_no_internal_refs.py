"""Customer-facing text carries no internal pointers.

Skills, README, SETUP and the agent-rules templates are read by external
users' assistants. Internal ticket ids (FW-…-1 style board ids), monorepo
paths (company/, workspace/packages, server/…, tickets/) and links into the
private monorepo tell them nothing; the technical fact stays, the pointer
goes.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted(
    list((ROOT / "symbols_mcp" / "skills").glob("*.md"))
    + [ROOT / "README.md", ROOT / "SETUP.md"]
    + [p for p in (ROOT / "templates").rglob("*") if p.is_file() and p.suffix in {".md", ".sh", ""}]
)

BOARD_ID = re.compile(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+-[0-9]+\b")
ALLOWED_IDS = {"UTF-8", "ISO-8859-1"}
INTERNAL_PATH = re.compile(r"(?:\bcompany/packages|\bworkspace/packages|\bserver/(?:workers|packages)|\btickets/|\]\(\.\./(?:server|workspace|smbls)/)")


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_board_ids_or_monorepo_paths(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    ids = sorted(set(BOARD_ID.findall(text)) - ALLOWED_IDS)
    assert not ids, ids
    assert not INTERNAL_PATH.search(text), INTERNAL_PATH.search(text).group(0)
