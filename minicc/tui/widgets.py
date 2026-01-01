"""
MiniCC TUI 组件

说明：本版本将"工具调用状态更新"作为一等能力，ToolCallLine/SubAgentLine 支持状态刷新。
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from textual.message import Message
from textual.widgets import Static

from minicc.core.models import DiffLine, TodoItem


@dataclass
class ToolCallItem:
    """工具调用项"""
    tool_call_id: str
    tool_name: str
    args: dict | None
    status: str = "running"  # running, completed, failed


@dataclass
class TaskWithTools:
    """带工具列表的任务"""
    todo: TodoItem
    tools: list[ToolCallItem] = field(default_factory=list)
    expanded: bool = True  # 是否展开


class TaskToolDisplay(Static):
    """任务与工具合并显示组件

    支持功能：
    - 每个任务下显示关联的工具调用
    - 任务可折叠/展开（点击切换）
    - 进行中任务有动画效果
    """

    class ToggleExpand(Message):
        """切换展开/折叠状态"""
        pass

    # 动画配置
    _ANIMATION_INTERVAL = 0.05  # 刷新间隔（秒）
    _PULSE_PERIOD = 2.0  # 脉冲周期（秒）

    def __init__(self, **kwargs):
        self.tasks_with_tools: list[TaskWithTools] = []
        self._timer = None
        self._current_active_task_index: int | None = None  # 跟踪当前活跃任务
        super().__init__(**kwargs)
        self._start_animation()

    def _start_animation(self) -> None:
        """启动动画定时器"""
        self._timer = self.set_timer(self._ANIMATION_INTERVAL, self._on_timer)

    def _on_timer(self) -> None:
        """定时器回调，周期性刷新实现动画效果"""
        self.refresh()
        self._timer = self.set_timer(self._ANIMATION_INTERVAL, self._on_timer)

    def _get_pulse_intensity(self) -> float:
        """计算当前脉冲强度 (0.0 ~ 1.0)"""
        phase = (time.time() % self._PULSE_PERIOD) / self._PULSE_PERIOD
        intensity = 0.65 + 0.35 * math.sin(2 * math.pi * phase)
        return intensity

    def _get_in_progress_style(self) -> str:
        """获取进行中任务的样式"""
        intensity = self._get_pulse_intensity()
        if intensity > 0.85:
            return "bold yellow"
        elif intensity > 0.7:
            return "yellow"
        elif intensity > 0.55:
            return "yellow dim"
        elif intensity > 0.4:
            return "yellow dim dim"
        else:
            return "dim yellow"

    def _get_loading_dots(self) -> str:
        """获取动态省略号"""
        cycle = int(time.time() * 2) % 3
        return "." * (cycle + 1)

    def update_todos(self, todos: list[TodoItem]) -> None:
        """更新任务列表，保留已有任务的工具关联，并更新活跃任务索引"""
        # 创建旧的 todo -> TaskWithTools 映射
        old_map = {tw.todo.content: tw for tw in self.tasks_with_tools}

        new_tasks: list[TaskWithTools] = []
        for i, todo in enumerate(todos):
            if todo.content in old_map:
                # 保留已有的任务及其工具
                tw = old_map[todo.content]
                tw.todo = todo
                new_tasks.append(tw)
                # 更新活跃任务索引
                if todo.status == "in_progress":
                    self._current_active_task_index = i
            else:
                # 新任务
                new_tasks.append(TaskWithTools(todo=todo, tools=[]))
                # 新任务如果是 in_progress，更新活跃索引
                if todo.status == "in_progress":
                    self._current_active_task_index = i

        # 如果没有 in_progress 的任务，重置活跃索引
        if not any(t.todo.status == "in_progress" for t in new_tasks):
            self._current_active_task_index = None

        self.tasks_with_tools = new_tasks
        self.refresh()

    def add_tool_call(self, tool_call_id: str, tool_name: str, args: dict | None) -> None:
        """添加工具调用到当前活跃任务"""
        # 优先使用活跃任务索引
        if self._current_active_task_index is not None:
            if 0 <= self._current_active_task_index < len(self.tasks_with_tools):
                tw = self.tasks_with_tools[self._current_active_task_index]
                tool = ToolCallItem(
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    args=args,
                    status="running"
                )
                tw.tools.append(tool)
                self.refresh()
                return

        # 备用方案：找到第一个 in_progress 或最后一个 pending 任务
        for i, tw in enumerate(self.tasks_with_tools):
            if tw.todo.status == "in_progress":
                tool = ToolCallItem(
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    args=args,
                    status="running"
                )
                tw.tools.append(tool)
                self._current_active_task_index = i  # 更新活跃索引
                self.refresh()
                return

        # 如果没有 in_progress，添加到最后一个 pending 任务
        for i in range(len(self.tasks_with_tools) - 1, -1, -1):
            if self.tasks_with_tools[i].todo.status == "pending":
                tool = ToolCallItem(
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    args=args,
                    status="running"
                )
                self.tasks_with_tools[i].tools.append(tool)
                self.refresh()
                return

    def update_tool_call(self, tool_call_id: str, status: str) -> None:
        """更新工具调用状态"""
        for tw in self.tasks_with_tools:
            for tool in tw.tools:
                if tool.tool_call_id == tool_call_id:
                    tool.status = status
                    self.refresh()
                    return

    def get_in_progress_task_index(self) -> int | None:
        """获取进行中任务的索引"""
        for i, tw in enumerate(self.tasks_with_tools):
            if tw.todo.status == "in_progress":
                return i
        return None

    def toggle_task_expand(self, index: int) -> None:
        """切换任务的展开/折叠状态"""
        if 0 <= index < len(self.tasks_with_tools):
            self.tasks_with_tools[index].expanded = not self.tasks_with_tools[index].expanded
            self.refresh()

    async def on_click(self, event) -> None:
        """处理点击事件：点击任务标题切换展开/折叠"""
        # 简单实现：根据点击的 y 坐标判断点击了哪个任务
        line_height = 1  # 每行高度
        for i, tw in enumerate(self.tasks_with_tools):
            task_line_start = i * 3  # 每个任务约占3行（标题+工具）
            if task_line_start <= event.y < task_line_start + 1:
                self.toggle_task_expand(i)
                return

    def on_unmount(self) -> None:
        """组件卸载时清理定时器"""
        if self._timer is not None:
            self._timer.stop()

    def _render_tool_status(self, tool: ToolCallItem) -> Text:
        """渲染工具状态行"""
        text = Text()
        # 工具名称
        text.append(f"  🔧 {tool.tool_name}", style="cyan")
        # 参数摘要
        summary = self._get_tool_summary(tool.args)
        if summary:
            text.append(f" {summary}", style="dim")
        # 状态图标
        icon = {
            "running": " 🔄",
            "completed": " ✅",
            "failed": " ❌",
        }.get(tool.status, " ❓")
        style = {"completed": "green", "failed": "red", "running": "yellow"}.get(tool.status, "dim")
        text.append(icon, style=style)
        return text

    def _get_tool_summary(self, args: dict | None) -> str:
        """获取工具参数摘要"""
        if not args:
            return ""
        key_params = ["path", "file_path", "pattern", "command", "query", "prompt"]
        for key in key_params:
            if key in args:
                value = str(args[key])
                if len(value) > 20:
                    value = value[:20] + "..."
                return f"({value})"
        return ""

    def render(self) -> Panel:
        if not self.tasks_with_tools:
            return Panel(Text("暂无任务", style="dim"), title="📋 任务", border_style="dim")

        text = Text()
        total = len(self.tasks_with_tools)
        done = sum(1 for tw in self.tasks_with_tools if tw.todo.status == "completed")

        for idx, tw in enumerate(self.tasks_with_tools, 1):
            # 任务标题（树状结构）
            if tw.todo.status == "in_progress":
                pulse_style = self._get_in_progress_style()
                dots = self._get_loading_dots()
                text.append(f"{idx}. ", style="dim")
                text.append(f"{tw.todo.content}{dots}\n", style=pulse_style)
            elif tw.todo.status == "completed":
                text.append(f"{idx}. ", style="dim")
                text.append(f"{tw.todo.content}\n", style="green")
            else:  # pending
                text.append(f"{idx}. ", style="dim")
                text.append(f"{tw.todo.content}\n", style="dim")

            # 如果展开，显示工具列表（树状缩进）
            if tw.expanded and tw.tools:
                for tool_idx, tool in enumerate(tw.tools):
                    # 树状连接线
                    is_last = tool_idx == len(tw.tools) - 1
                    if is_last:
                        tree_prefix = "└── "
                    else:
                        tree_prefix = "├── "

                    # 工具状态图标
                    icon = {
                        "running": "🟠",
                        "completed": "🟢",
                        "failed": "🔴",
                    }.get(tool.status, "⚪")

                    # 工具名称
                    tool_text = Text()
                    tool_text.append(tree_prefix, style="dim")
                    tool_text.append(f"{icon} ", style="dim")
                    tool_text.append(tool.tool_name)

                    # 参数摘要
                    summary = self._get_tool_summary(tool.args)
                    if summary:
                        tool_text.append(f" {summary}", style="dim")

                    text.append_text(tool_text)
                    text.append("\n")

        all_done = done == total and total > 0
        title = "📋 任务 ✓ 全部完成" if all_done else f"📋 任务 [{done}/{total}]"
        border = "green" if all_done else "cyan"
        return Panel(text, title=title, title_align="left", border_style=border)


# 保留原有的其他组件
class MessagePanel(Static):
    def __init__(self, content: str, role: str = "user", **kwargs):
        self.role = role
        self._content = content
        super().__init__(content, markup=False, **kwargs)

    def set_content(self, content: str) -> None:
        self._content = content
        self.update(content)

    def render(self) -> Panel:
        role_style = {
            "user": ("blue", "You"),
            "assistant": ("green", "Assistant"),
            "system": ("magenta", "System"),
        }
        color, title = role_style.get(self.role, ("white", self.role.title()))
        markdown = Markdown(self._content or "", code_theme="monokai", justify="left")
        return Panel(markdown, title=title, border_style=color, expand=True)


class ToolCallLine(Static):
    def __init__(self, tool_name: str, args: dict | None, status: str = "running", **kwargs):
        self.tool_name = tool_name
        self.args = args or {}
        self.status = status
        super().__init__(**kwargs)

    def update_status(self, status: str) -> None:
        self.status = status
        self.refresh()

    def render(self) -> Text:
        text = Text()
        text.append("  🔧 ", style="yellow")
        text.append(self.tool_name, style="bold yellow")

        summary = self._get_summary()
        if summary:
            text.append(f" {summary}", style="dim")

        icon = {
            "pending": " ⏳",
            "running": " 🔄",
            "completed": " ✅",
            "failed": " ❌",
        }.get(self.status, " ❓")
        style = {"completed": "green", "failed": "red", "running": "yellow", "pending": "dim"}.get(
            self.status, "dim"
        )
        text.append(icon, style=style)
        return text

    def _get_summary(self) -> str:
        key_params = ["path", "file_path", "pattern", "command", "query", "prompt"]
        for key in key_params:
            if key in self.args:
                value = str(self.args[key])
                # 截断参数值，确保状态图标可见
                if len(value) > 25:
                    value = value[:25] + "..."
                return f"({value})"
        return ""


class SubAgentLine(Static):
    def __init__(self, task_id: str, prompt: str, status: str, **kwargs):
        self.task_id = task_id
        self.prompt = prompt
        self.status = status
        super().__init__(**kwargs)

    def update_status(self, status: str) -> None:
        self.status = status
        self.refresh()

    def render(self) -> Text:
        text = Text()
        text.append("  🤖 ", style="magenta")
        prompt_short = self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt
        text.append(prompt_short, style="bold magenta")
        icon = {
            "pending": " ⏳",
            "running": " 🔄",
            "completed": " ✅",
            "failed": " ❌",
        }.get(self.status, " ❓")
        text.append(icon)
        return text


class DiffView(Static):
    def __init__(self, diff_lines: list[DiffLine], filename: str = "", **kwargs):
        self.diff_lines = diff_lines
        self.filename = filename
        super().__init__(**kwargs)

    def render(self) -> Panel:
        text = Text()
        for line in self.diff_lines:
            if line.type == "add":
                text.append(f"+ {line.content}\n", style="green")
            elif line.type == "remove":
                text.append(f"- {line.content}\n", style="red")
            else:
                text.append(f"  {line.content}\n", style="dim")
        title = f"Diff: {self.filename}" if self.filename else "Diff"
        return Panel(text, title=title, border_style="cyan", expand=True)


class BottomBar(Static):
    def __init__(
        self,
        model: str = "",
        cwd: str = "",
        git_branch: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        **kwargs,
    ):
        self.model = model
        self.cwd = cwd
        self.git_branch = git_branch
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        super().__init__(**kwargs)

    def update_info(
        self,
        model: str | None = None,
        cwd: str | None = None,
        git_branch: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        if model is not None:
            self.model = model
        if cwd is not None:
            self.cwd = cwd
        if git_branch is not None:
            self.git_branch = git_branch
        if input_tokens is not None:
            self.input_tokens = input_tokens
        if output_tokens is not None:
            self.output_tokens = output_tokens
        self.refresh()

    def add_tokens(self, input_delta: int = 0, output_delta: int = 0) -> None:
        self.input_tokens += input_delta
        self.output_tokens += output_delta
        self.refresh()

    def render(self) -> Text:
        text = Text()
        text.append(" 📦 ", style="dim")
        text.append(self.model or "N/A", style="cyan")
        text.append("  │  ", style="dim")

        text.append("📁 ", style="dim")
        cwd_short = self.cwd
        if len(cwd_short) > 25:
            cwd_short = "..." + cwd_short[-22:]
        text.append(cwd_short, style="green")
        text.append("  │  ", style="dim")

        text.append("🌿 ", style="dim")
        text.append(self.git_branch or "N/A", style="magenta" if self.git_branch else "dim")
        text.append("  │  ", style="dim")

        # 说明：部分终端/字体对 emoji（如 ⬆️/⬇️）支持不佳，容易显示为方块或宽度异常；
        # 因此使用更通用的箭头字符。
        text.append("↑", style="dim")
        text.append(f"{self.input_tokens}", style="yellow")
        text.append(" ↓", style="dim")
        text.append(f"{self.output_tokens}", style="yellow")
        return text


# 保留旧的 TodoDisplay 作为别名（向后兼容）
TodoDisplay = TaskToolDisplay
