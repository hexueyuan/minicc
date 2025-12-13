from __future__ import annotations

import json
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.toolsets import ToolsetTool, WrapperToolset

from .schemas import MiniCCDeps, ToolResult


def _stringify_result(value: Any, max_len: int = 2000) -> str:
    if value is None:
        return "OK"
    if isinstance(value, str):
        return value if len(value) <= max_len else value[:max_len] + "…"
    try:
        text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    except Exception:
        text = str(value)
    return text if len(text) <= max_len else text[:max_len] + "…"


class MCPUICallbackToolset(WrapperToolset[MiniCCDeps]):
    """
    给任意 toolset 增加 UI 回调：

    MiniCC 的 UI 工具提示依赖 `deps.on_tool_call`，但 MCP 工具调用不经过 `minicc.tools._finalize`，
    因此默认不会出现在界面里。这个 wrapper 在每次调用 tool 时补齐回调。
    """

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[MiniCCDeps],
        tool: ToolsetTool[MiniCCDeps],
    ) -> Any:
        callback = getattr(ctx.deps, "on_tool_call", None)
        try:
            result = await self.wrapped.call_tool(name, tool_args, ctx, tool)
        except Exception as e:
            if callback:
                try:
                    callback(name, tool_args, ToolResult(success=False, output="", error=str(e)))
                except Exception:
                    pass
            raise

        if callback:
            try:
                callback(name, tool_args, ToolResult(success=True, output=_stringify_result(result), error=None))
            except Exception:
                pass

        return result
