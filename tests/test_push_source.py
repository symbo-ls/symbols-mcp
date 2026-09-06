"""Push-source declaration contract
(FW-CLI-PUSH-DECLARES-SOURCE-IDENTITY-FORCE-LIBRARY-FLAG-1, parent
CORE-PUSH-WITH-A-FOREIGN-OWNER-KEY-LANDED-ON-THE-SYSTEM-BRAND-SHARED-LIBRARY-1).

Every `save_to_project` write to `POST /core/projects/:id/changes` must
declare `body.source = { owner?, key?, lockProjectId?, client }` so the
server's PushSourceGuard can refuse a cross-owner replay and gate
shared-library writes on possession of the record's id. These tests pin the
client half: what gets declared, from where, and that the force flag reaches
the wire only as a literal True.
"""

import importlib
import json


server = importlib.import_module("symbols_mcp.server")


def test_client_string_is_versioned():
    client = server._mcp_client_string()
    assert client.startswith("symbols-mcp@")
    assert client != "symbols-mcp@"


def test_key_heuristic_shared_with_resolver():
    assert server._looks_like_project_key("pr_abc123")
    assert server._looks_like_project_key("brand")
    assert server._looks_like_project_key("system/brand")
    # A raw 24-hex ObjectId is NOT a key — no owner/key claim may be built
    # from it.
    assert not server._looks_like_project_key("688e2195d3646fd6ae415464")


def test_source_declares_owner_and_key_from_two_seg_argument():
    src = server._build_push_source("system/brand")
    assert src["owner"] == "system"
    assert src["key"] == "brand"
    assert src["client"].startswith("symbols-mcp@")


def test_source_declares_only_key_from_bare_key_argument():
    src = server._build_push_source("brand")
    assert src.get("key") == "brand"
    assert "owner" not in src


def test_source_makes_no_identity_claim_from_a_raw_object_id():
    # The incident vector was an id trusted verbatim — an id argument must
    # never fabricate an owner/key declaration the caller did not make.
    src = server._build_push_source("688e2195d3646fd6ae415464")
    assert "owner" not in src
    assert "key" not in src
    assert src["client"].startswith("symbols-mcp@")


def test_lock_project_id_read_from_cwd_tree(tmp_path, monkeypatch):
    (tmp_path / "symbols.json").write_text(json.dumps({"owner": "system", "key": "brand"}))
    local = tmp_path / ".symbols_local"
    local.mkdir()
    (local / "lock.json").write_text(json.dumps({"projectId": "688e2195d3646fd6ae415464"}))
    monkeypatch.chdir(tmp_path)
    src = server._build_push_source("system/brand")
    assert src["lockProjectId"] == "688e2195d3646fd6ae415464"


def test_lock_project_id_omitted_when_tree_has_none(tmp_path, monkeypatch):
    (tmp_path / "symbols.json").write_text(json.dumps({"owner": "system", "key": "brand"}))
    monkeypatch.chdir(tmp_path)
    src = server._build_push_source("system/brand")
    assert "lockProjectId" not in src


def test_save_to_project_signature_carries_force_flag():
    import inspect

    sig = inspect.signature(server.save_to_project)
    param = sig.parameters.get("force_shared_library")
    assert param is not None
    assert param.default is False
