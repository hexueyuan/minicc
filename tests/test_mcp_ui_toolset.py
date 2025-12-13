from __future__ import annotations

from typing import Any

import pytest
from pydantic_core import SchemaValidator, core_schema
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import RunContext, ToolDefinition
from pydantic_ai.toolsets import AbstractToolset, ToolsetTool

from minicc.mcp_ui_toolset import MCPUICallbackToolset
from minicc.schemas import Config, MiniCCDeps, Provider


class _EchoToolset(AbstractToolset[MiniCCDeps]):
    @property
    def id(self) -> str | None:
        return "echo"

    async def get_tools(self, ctx: RunContext[MiniCCDeps]) -> dict[str, ToolsetTool[MiniCCDeps]]:
        validator = SchemaValidator(core_schema.any_schema())
        return {
            "echo": ToolsetTool(
                toolset=self,
                tool_def=ToolDefinition(
                    name="echo",
                    description="echo args",
                    parameters_json_schema={
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                    },
                ),
                max_retries=1,
                args_validator=validator,
            )
        }

    async def call_tool(
        self, name: str, tool_args: dict[str, Any], ctx: RunContext[MiniCCDeps], tool: ToolsetTool[MiniCCDeps]
    ) -> Any:
        assert name == "echo"
        return tool_args["text"]


@pytest.mark.asyncio
async def test_mcp_ui_callback_toolset_emits_on_tool_call():
    calls: list[tuple[str, dict, Any]] = []

    def on_tool_call(tool_name: str, args: dict, result: Any) -> None:
        calls.append((tool_name, args, result))

    deps = MiniCCDeps(config=Config(provider=Provider.ANTHROPIC, model="x", api_key="x"), cwd=".", fs=None)
    deps.on_tool_call = on_tool_call

    agent = Agent(
        model=TestModel(call_tools=["echo"], custom_output_text="ok"),
        deps_type=MiniCCDeps,
        toolsets=[MCPUICallbackToolset(_EchoToolset())],
    )
    await agent.run("hi", deps=deps)

    assert len(calls) == 1
    name, args, result = calls[0]
    assert name == "echo"
    assert args["text"]  # 由 TestModel 生成
    assert hasattr(result, "success")
