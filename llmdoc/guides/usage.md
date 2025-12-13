# 使用指南

## 安装

```bash
# 使用 uv
uv pip install minicc

# 使用 pip
pip install minicc
```

## 配置 API Key

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-xxx"

# OpenAI
export OPENAI_API_KEY="sk-xxx"
```

## 启动应用

```bash
# 命令行启动
minicc

# 或使用 Python 模块
python -m minicc
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Enter | 发送消息 |
| Ctrl+C | 退出应用 |
| Ctrl+L | 清屏 |
| Escape | 取消当前操作 |

## 配置文件

### ~/.minicc/config.json

```json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "api_key": null
}
```

### MCP 配置（可选）

MiniCC 会在运行时加载 MCP 服务器，并将其工具注入到 Agent 中。

MCP 工具的调用也会像内置工具一样在 UI 中显示“🔧 工具调用”提示。

如需启用 MCP（连接/启动 MCP servers），请确保安装了可选依赖：

```bash
# pip
pip install "minicc[mcp]"

# uv
uv pip install "minicc[mcp]"
```

未安装 MCP 依赖时，MiniCC 会告警并自动降级为“不加载 MCP”，不会影响应用启动。

配置文件位置优先级：

1. 工作目录下的 `.minicc/mcp.json`
2. 全局 `~/.minicc/mcp.json`

注意：MiniCC 启动时会基于启动目录（cwd）决定使用哪一份 MCP 配置；如果你在别的目录启动，可能会命中全局配置而非项目配置。

配置格式与 pydantic-ai 的 MCP 配置一致，例如：

```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"]
    },
    "local_http": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

其中：

- `command`/`args` 表示通过 stdio 启动的 MCP server。
- `url` 表示通过 HTTP/SSE/Streamable HTTP 连接的 MCP server。
- 支持 `${ENV_VAR}` 或 `${ENV_VAR:-default}` 形式的环境变量展开。

### ~/.minicc/AGENTS.md

自定义系统提示词，可以修改 Agent 的行为和工具使用策略。

## 编程接口

```python
import asyncio
from minicc import create_agent, MiniCCDeps, load_config

async def main():
    config = load_config()
    deps = MiniCCDeps(config=config, cwd="/path/to/project")
    agent = create_agent(config, cwd=deps.cwd)

    result = await agent.run("你的问题", deps=deps)
    print(result.data)

asyncio.run(main())
```

## 开发调试

```bash
# 使用 textual 开发模式
uv run textual run --dev minicc.app:MiniCCApp

# 在另一个终端查看日志
textual console
```

### 错误堆栈显示（Debug）

默认情况下，MiniCC 只在界面中显示简短错误信息。若你需要在 TUI 中直接看到完整 traceback，可设置：

```bash
export MINICC_DEBUG=1
minicc
```
