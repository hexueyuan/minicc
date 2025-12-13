from __future__ import annotations

from pathlib import Path

from minicc import config as config_mod


def test_find_mcp_config_prefers_project(temp_dir: Path, monkeypatch):
    project_cfg = temp_dir / config_mod.PROJECT_CONFIG_DIRNAME / config_mod.PROJECT_MCP_CONFIG_NAME
    project_cfg.parent.mkdir(parents=True, exist_ok=True)
    project_cfg.write_text('{"mcpServers": {}}', encoding="utf-8")

    global_cfg = temp_dir / "global_mcp.json"
    global_cfg.write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setattr(config_mod, "MCP_CONFIG_FILE", global_cfg)

    assert config_mod.find_mcp_config(temp_dir) == project_cfg


def test_find_mcp_config_fallbacks_to_global(temp_dir: Path, monkeypatch):
    global_cfg = temp_dir / "global_mcp.json"
    global_cfg.write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setattr(config_mod, "MCP_CONFIG_FILE", global_cfg)

    assert config_mod.find_mcp_config(temp_dir) == global_cfg


def test_find_mcp_config_returns_none_when_missing(temp_dir: Path, monkeypatch):
    global_cfg = temp_dir / "global_mcp.json"
    monkeypatch.setattr(config_mod, "MCP_CONFIG_FILE", global_cfg)

    assert config_mod.find_mcp_config(temp_dir) is None

