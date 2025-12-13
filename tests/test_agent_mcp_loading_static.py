from __future__ import annotations

import builtins
from pathlib import Path

from minicc.agent import create_agent
from minicc.schemas import Config, Provider


def test_create_agent_mcp_import_error_is_non_fatal(temp_dir: Path, monkeypatch):
    cfg_dir = temp_dir / ".minicc"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "mcp.json").write_text('{"mcpServers": {"x": {"command": "noop", "args": []}}}', encoding="utf-8")

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pydantic_ai.mcp":
            raise ImportError("missing mcp dependency")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    agent = create_agent(
        Config(provider=Provider.ANTHROPIC, model="test", api_key="test"),
        cwd=temp_dir,
    )
    assert agent is not None

