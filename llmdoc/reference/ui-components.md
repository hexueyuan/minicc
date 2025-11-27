# UI 组件参考

本文档提供 MiniCC 自定义 UI 组件的接口说明。

## MessagePanel

**文件:** `minicc/ui/widgets.py:17-59`

显示用户或助手的单条消息，支持 Markdown 渲染。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| content | str | 消息内容（Markdown） |
| role | str | "user" \| "assistant" \| "system" |

**方法:** `set_content(content: str)` - 更新内容

**角色样式:** user(蓝) / assistant(绿) / system(洋红)

## ToolCallLine

**文件:** `minicc/ui/widgets.py:44-85`

工具调用单行显示，简洁展示执行状态。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| tool_name | str | 工具名称 |
| args | dict | 调用参数 |
| status | str | "pending" \| "running" \| "completed" \| "failed" |
| result | Optional[Any] | 执行结果 |

**显示格式:** `🔧 {tool_name} ({key_param}) {status_icon}`

**参数选择优先级:** path > file_path > pattern > command > query > prompt (30字符截断)

**状态图标:**
- `⏳` (pending)
- `🔄` (running)
- `✅` (completed)
- `❌` (failed)

## SubAgentLine

**文件:** `minicc/ui/widgets.py:87-127`

SubAgent 任务单行显示，简洁展示子任务状态。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | str | 任务 ID |
| prompt | str | 任务描述 |
| status | str | "pending" \| "running" \| "completed" \| "failed" |
| result | Optional[str] | 任务结果 |

**显示格式:** `🤖 {prompt摘要} {status_icon}`

**提示词截断:** 40 字符

**状态图标:**
- `⏳` (pending)
- `🔄` (running)
- `✅` (completed)
- `❌` (failed)

## DiffView

**文件:** `minicc/ui/widgets.py:129-189`

显示文件变更的 Diff 视图，支持颜色区分。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| diff_lines | list[DiffLine] | Diff 行列表 |
| filename | Optional[str] | 可选文件名 |

**DiffLine 结构 (schemas.py):**
```python
class DiffLine:
    type: str  # "add" | "remove" | "context"
    content: str  # 行内容
    line_no: Optional[int]  # 行号
```

**显示样式:**
- `add` (绿色 `+`)
- `remove` (红色 `-`)
- `context` (暗灰色 ` `)

## BottomBar

**文件:** `minicc/ui/widgets.py:191-230`

底边栏，恒定显示关键上下文信息（模型/目录/分支/Token）。

**参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| model | str | provider:model (如 `anthropic:claude-sonnet-4`) |
| cwd | str | 工作目录（超长时显示尾部） |
| git_branch | Optional[str] | Git 分支名 |
| input_tokens | int | 累计输入 token 数 |
| output_tokens | int | 累计输出 token 数 |

**方法:**
- `update_info(**kwargs)` - 更新任何字段（支持 model, cwd, git_branch, input_tokens, output_tokens）
- `add_tokens(input_delta, output_delta)` - 累加 token 数

**显示格式:**
```
📦 anthropic:claude-sonnet-4 │ 📁 /home/user/proj │ 🌿 main │ ⬆️123 ⬇️456
```

**设计特点:**
- 恒定显示，不可折叠
- 实时更新（接收 AgentRunResultEvent）
- 超长目录自动截断，显示尾部路径

## 已弃用组件

v1.0 重构移除了以下组件（已被新组件替代）：

- `ToolCallPanel` (行 62-116) → 被 `ToolCallLine` 替代
- `CollapsibleToolPanel` (已删除) → 被 `ToolCallLine` 替代
- `UsageDisplay` (行 162-192) → 功能集成到 `BottomBar`
- `StatusBar` (行 195-223) → 功能已弃用
- `SubAgentPanel` (已删除) → 被 `SubAgentLine` 替代

**迁移说明:**
- 这些组件已从代码库移除
- 所有功能已由新组件实现
- 无须维护向后兼容性

## 工具调用回调

**文件:** `minicc/app.py:175-202` (`_on_tool_call`)

工具执行后自动调用的回调函数：

```python
def _on_tool_call(self, tool_name: str, args: dict, result: Any) -> None:
    """处理工具调用，mount 对应的 UI 组件"""
```

**行为:**
- `spawn_agent` 工具 → mount `SubAgentLine` 组件
- 其他工具 → mount `ToolCallLine` 组件
- 自动 mount 到 chat_container（消息流中）
- 自动滚动到底部

**依赖注入:**
- 通过 `MiniCCDeps.on_tool_call` 传入 Agent
- 由 `tools.py` 中的工具函数调用

## 集成指南

创建新组件步骤：

1. **定义组件** (minicc/ui/widgets.py)
   - 继承 `Static` 或 `Collapsible`
   - 实现 `render()` 或 `compose()` 方法
   - 添加 `__init__()` 方法初始化参数

2. **导出组件** (minicc/ui/__init__.py)
   - 添加到 `__all__` 列表
   - 在文件顶部导入

3. **定义样式** (minicc/ui/styles.tcss)
   - 使用选择器 `<ComponentName>`
   - 定义颜色、宽度、边框等

4. **使用组件** (minicc/app.py)
   - 导入组件类
   - 使用 `self.query_one(selector).mount(component_instance)`
   - 或直接在 `compose()` 中使用 `yield`

**示例:**
```python
# widgets.py
class MyComponent(Static):
    def render(self) -> str:
        return "Hello"

# __init__.py
from .widgets import MyComponent
__all__ = [..., "MyComponent"]

# styles.tcss
MyComponent { width: 100%; }

# app.py
from .ui import MyComponent
container.mount(MyComponent())
```
