"""
MiniCC TUI 组件

说明：本版本将"工具调用状态更新"作为一等能力，ToolCallLine/SubAgentLine 支持状态刷新。
"""

from __future__ import annotations

import math
import time

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from textual.message import Message
from textual.widgets import Static

from minicc.core.models import DiffLine, TodoItem


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
                if len(value) > 40:
                    value = value[:40] + "..."
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


class TodoDisplay(Static):
    """任务显示组件，支持进行中任务的平滑脉冲动画效果和自动滚动"""

    class Closed(Message):
        pass

    # 动画配置
    _ANIMATION_INTERVAL = 0.05  # 刷新间隔（秒）
    _PULSE_PERIOD = 2.0  # 脉冲周期（秒）

    def __init__(self, todos: list[TodoItem] | None = None, **kwargs):
        self.todos: list[TodoItem] = todos or []
        self._timer = None
        self._last_in_progress_index: int | None = None
        super().__init__(**kwargs)
        # 启动动画定时器
        self._start_animation()

    def _start_animation(self) -> None:
        """启动动画定时器"""
        self._timer = self.set_timer(self._ANIMATION_INTERVAL, self._on_timer)

    def _on_timer(self) -> None:
        """定时器回调，周期性刷新实现动画效果"""
        self.refresh()
        self._timer = self.set_timer(self._ANIMATION_INTERVAL, self._on_timer)

    def _get_pulse_intensity(self) -> float:
        """
        计算当前脉冲强度 (0.0 ~ 1.0)

        使用正弦波实现平滑的呼吸效果：
        - 值在 0.3 ~ 1.0 之间循环
        - 周期为 _PULSE_PERIOD 秒
        """
        phase = (time.time() % self._PULSE_PERIOD) / self._PULSE_PERIOD  # 0.0 ~ 1.0
        # 正弦波：-1 ~ 1 -> 映射到 0.3 ~ 1.0
        intensity = 0.65 + 0.35 * math.sin(2 * math.pi * phase)
        return intensity

    def _get_in_progress_style(self) -> str:
        """
        根据脉冲强度获取进行中任务的样式

        返回不同层级的黄色样式以实现平滑过渡
        """
        intensity = self._get_pulse_intensity()

        # 将 0.3 ~ 1.0 的强度映射到 5 个层级
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
        """
        获取动态省略号

        返回 ".", "..", "..." 循环变化
        每 500ms 变化一次
        """
        cycle = int(time.time() * 2) % 3  # 0, 1, 2 循环（每秒2次变化）
        return "." * (cycle + 1)

    def _find_in_progress_index(self) -> int | None:
        """查找进行中任务的索引"""
        for i, todo in enumerate(self.todos):
            if todo.status == "in_progress":
                return i
        return None

    def _scroll_to_in_progress(self) -> None:
        """滚动到进行中的任务（使其居中）"""
        in_progress_index = self._find_in_progress_index()
        if in_progress_index is None:
            return

        # 如果进行中的任务位置发生变化，则滚动
        if in_progress_index != self._last_in_progress_index:
            self._last_in_progress_index = in_progress_index
            # 尝试滚动到该任务（使其居中可见）
            self.scroll_to_widget(self, animate=False)

    def update_todos(self, todos: list[TodoItem]) -> None:
        self.todos = todos
        in_progress_index = self._find_in_progress_index()
        if in_progress_index != self._last_in_progress_index:
            self._last_in_progress_index = in_progress_index
        self.refresh()

    def is_all_completed(self) -> bool:
        if not self.todos:
            return False
        return all(t.status == "completed" for t in self.todos)

    async def on_click(self, event) -> None:
        if self.is_all_completed():
            if event.x >= self.size.width - 6:
                self.post_message(self.Closed())

    def on_unmount(self) -> None:
        """组件卸载时清理定时器"""
        if self._timer is not None:
            self._timer.stop()

    def render(self) -> Panel:
        if not self.todos:
            return Panel(Text("暂无任务", style="dim"), title="📋 任务", border_style="dim")

        text = Text()
        total = len(self.todos)
        done = sum(1 for t in self.todos if t.status == "completed")

        # 统一列表视图，按原始顺序显示所有任务
        for todo in self.todos:
            if todo.status == "in_progress":
                # 进行中：黄色脉冲 + 动态省略号
                pulse_style = self._get_in_progress_style()
                dots = self._get_loading_dots()
                text.append(f"{todo.content}{dots}\n", style=pulse_style)
            elif todo.status == "completed":
                # 已完成：绿色
                text.append(f"{todo.content}\n", style="green")
            else:  # pending
                # 未开始：灰色
                text.append(f"{todo.content}\n", style="dim")

        all_done = done == total and total > 0
        title = "📋 任务 ✓ 全部完成 [×]" if all_done else f"📋 任务 [{done}/{total}]"
        border = "green" if all_done else "cyan"
        return Panel(text, title=title, title_align="left", border_style=border)
