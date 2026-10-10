"""The Python server reports the package version in initialize.serverInfo.

FastMCP's constructor has no `version=` passthrough, so the low-level Server
it builds internally falls back to `importlib.metadata.version("mcp")` — the
SDK's own version (e.g. '1.30.0'), not the symbols-mcp package version —
unless `symbols_mcp.server` sets `mcp._mcp_server.version` explicitly after
construction. Mirrors the Node fix (symbols-mcp f6280cf,
test_node_server_info_version.py).
"""

import importlib
from importlib.metadata import version as pkg_version

server = importlib.import_module("symbols_mcp.server")


def test_server_info_version_is_package_version():
    opts = server.mcp._mcp_server.create_initialization_options()
    assert opts.server_version == server.PACKAGE_VERSION
    assert opts.server_version != pkg_version("mcp")
