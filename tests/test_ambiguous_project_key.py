"""A bare project key the Symbols API finds under more than one owner.

Since the server change of 2026-10-24 the 1-seg by-key routes answer such a
key 409 `{"error": "ambiguous_key", "candidates": [{"owner", "key"}]}` and
never pick one. The tools used to report it as "Project 'fly' not found:
ambiguous_key" / "Failed to get project data: ambiguous_key" — nothing the
assistant could act on. They now name the owner/key pairs and ask for one.

The Python server is driven with its API call replaced; the Node server
(`bin/symbols-mcp.cjs`) over stdio JSON-RPC against a stand-in API
(SYMBOLS_API_URL), the way an MCP client talks to it.
"""

import asyncio
import importlib
import json
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

server = importlib.import_module("symbols_mcp.server")

ROOT = Path(__file__).resolve().parent.parent
NODE_SERVER = ROOT / "bin" / "symbols-mcp.cjs"

AMBIGUOUS = {
    "error": "ambiguous_key",
    "message": "Project key matches more than one project",
    "candidates": [{"owner": "acme", "key": "fly"}, {"owner": "globex", "key": "fly"}],
}


def _fake_api(monkeypatch, seen):
    async def fake(method, path, token="", api_key="", body=None):
        seen.append(path)
        if path.startswith("/core/projects/key/fly"):
            return dict(AMBIGUOUS)
        if path.startswith("/core/projects/key/acme/fly"):
            return {"success": True, "data": {"_id": "64b0000000000000000000c1", "components": {"Hero": {}}}}
        return {"success": False, "error": "not_found"}

    monkeypatch.setattr(server, "_api_request", fake)


def test_resolver_names_the_candidates(monkeypatch):
    seen = []
    _fake_api(monkeypatch, seen)
    project_id, err = asyncio.run(server._resolve_project_id("fly", token="t"))
    assert project_id == ""
    assert "acme/fly, globex/fly" in err
    assert "not found" not in err


def test_resolver_takes_owner_and_key(monkeypatch):
    seen = []
    _fake_api(monkeypatch, seen)
    project_id, err = asyncio.run(server._resolve_project_id("acme/fly", token="t"))
    assert err is None
    assert project_id == "64b0000000000000000000c1"
    assert seen == ["/core/projects/key/acme/fly"]


def test_message_without_candidates_still_asks_for_owner_and_key():
    msg = server._ambiguous_key_message("fly", {"error": "ambiguous_key"})
    assert "owner/key" in msg
    assert server._ambiguous_key_message("fly", {"error": "project_unavailable"}) is None


class _StandIn(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 — http.server's own name
        if self.path.startswith("/core/projects/key/fly"):
            status, body = 409, AMBIGUOUS
        else:
            status, body = 404, {"error": "not_found"}
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_node_server_names_the_candidates():
    httpd = HTTPServer(("127.0.0.1", 0), _StandIn)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        lines = [
            json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "get_project", "arguments": {"project": "fly", "token": "t"}}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "publish", "arguments": {"project": "fly", "token": "t"}}}),
        ]
        env = {"PATH": __import__("os").environ.get("PATH", ""),
               "SYMBOLS_API_URL": f"http://127.0.0.1:{httpd.server_address[1]}"}
        proc = subprocess.run(["node", str(NODE_SERVER)], input="\n".join(lines) + "\n",
                              capture_output=True, text=True, timeout=60, env=env)
        replies = {}
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                msg = json.loads(line)
                replies[msg.get("id")] = msg
        for rid in (1, 2):
            text = json.dumps(replies.get(rid, {}))
            assert "acme/fly, globex/fly" in text, f"reply {rid}: {text[:400]}"
    finally:
        httpd.shutdown()
