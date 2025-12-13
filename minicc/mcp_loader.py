"""
MiniCC MCP 加载器

负责：
- 查找 MCP 配置（项目级/全局）
- 惰性导入 pydantic_ai.mcp，确保缺少依赖时不会导致 MiniCC 启动失败
- 将 MCP tool 调用接入 MiniCC 的 on_tool_call 回调（用于 UI 显示工具调用提示）
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

from pydantic_ai.toolsets import AbstractToolset

from .config import find_mcp_config
from .mcp_ui_toolset import MCPUICallbackToolset


def load_mcp_toolsets(cwd: str | Path | None) -> list[AbstractToolset[Any]]:
    """
    加载 MCP servers（以 toolsets 形式返回，直接传给 pydantic-ai Agent）。

    说明：
    - 返回值为空列表表示“未启用/未加载 MCP”。
    - 使用静态 toolsets（而非 agent.toolset 动态加载），避免 anyio CancelScope 跨 Task 退出报错。
    """
    base = cwd if cwd is not None else os.getcwd()
    config_path = find_mcp_config(base)
    if not config_path:
        return []

    try:
        from pydantic_ai.mcp import load_mcp_servers  # 惰性导入
    except Exception as e:
        warnings.warn(f"加载 MCP 失败：未安装 MCP 依赖或导入异常：{e}")
        return []

    try:
        servers = load_mcp_servers(config_path)
    except Exception as e:
        warnings.warn(f"加载 MCP 失败：配置文件 {config_path} 解析/展开环境变量异常：{e}")
        return []

    return [MCPUICallbackToolset(s) for s in list(servers or [])]

