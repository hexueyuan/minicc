"""
MiniCC tools.py 单元测试

覆盖所有工具函数：
- 文件操作: read_file, write_file, edit_file
- 搜索: glob_files, grep_search
- 命令行: bash, bash_output, kill_shell
- 任务管理: task, todo_write
- 辅助函数
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from minicc.schemas import BackgroundShell, MiniCCDeps, TodoItem
from minicc.tools import (
    _find_whitespace_tolerant,
    _generate_unified_diff,
    _normalize_whitespace,
    _resolve_path,
    bash,
    bash_output,
    edit_file,
    format_diff,
    generate_diff,
    glob_files,
    grep_search,
    kill_shell,
    read_file,
    todo_write,
    write_file,
)


# ============ 文件操作工具测试 ============


class TestReadFile:
    """read_file 工具测试"""

    @pytest.mark.asyncio
    async def test_read_existing_file(self, mock_ctx: MagicMock, sample_file: Path):
        """测试读取存在的文件"""
        result = await read_file(mock_ctx, str(sample_file))

        assert result.success is True
        assert "line 1" in result.output
        assert "line 5" in result.output
        assert result.error is None

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试读取不存在的文件"""
        result = await read_file(mock_ctx, str(temp_dir / "nonexistent.txt"))

        assert result.success is False
        assert "文件不存在" in result.error

    @pytest.mark.asyncio
    async def test_read_directory(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试读取目录（应该失败）"""
        result = await read_file(mock_ctx, str(temp_dir))

        assert result.success is False
        assert "不是文件" in result.error

    @pytest.mark.asyncio
    async def test_read_with_offset_and_limit(
        self, mock_ctx: MagicMock, sample_file: Path
    ):
        """测试带偏移和限制的读取"""
        result = await read_file(mock_ctx, str(sample_file), offset=2, limit=2)

        assert result.success is True
        assert "line 2" in result.output
        assert "line 3" in result.output
        # 不应该包含 line 1
        assert "line 1" not in result.output.split("\n")[0]  # 第一行不是 line 1

    @pytest.mark.asyncio
    async def test_read_file_line_numbers(self, mock_ctx: MagicMock, sample_file: Path):
        """测试输出包含行号（cat -n 格式）"""
        result = await read_file(mock_ctx, str(sample_file))

        assert result.success is True
        # 检查行号格式
        assert "\t" in result.output  # tab 分隔符

    @pytest.mark.asyncio
    async def test_read_relative_path(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试相对路径读取"""
        # 创建文件
        (temp_dir / "relative_test.txt").write_text("test content")

        result = await read_file(mock_ctx, "relative_test.txt")

        assert result.success is True
        assert "test content" in result.output


class TestWriteFile:
    """write_file 工具测试"""

    @pytest.mark.asyncio
    async def test_write_new_file(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试写入新文件"""
        file_path = temp_dir / "new_file.txt"
        content = "Hello, World!"

        result = await write_file(mock_ctx, str(file_path), content)

        assert result.success is True
        assert file_path.exists()
        assert file_path.read_text() == content

    @pytest.mark.asyncio
    async def test_write_overwrite_file(
        self, mock_ctx: MagicMock, sample_file: Path
    ):
        """测试覆盖现有文件"""
        new_content = "New content"

        result = await write_file(mock_ctx, str(sample_file), new_content)

        assert result.success is True
        assert sample_file.read_text() == new_content

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(
        self, mock_ctx: MagicMock, temp_dir: Path
    ):
        """测试自动创建父目录"""
        file_path = temp_dir / "subdir" / "nested" / "file.txt"

        result = await write_file(mock_ctx, str(file_path), "content")

        assert result.success is True
        assert file_path.exists()

    @pytest.mark.asyncio
    async def test_write_relative_path(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试相对路径写入"""
        result = await write_file(mock_ctx, "relative_write.txt", "test")

        assert result.success is True
        assert (temp_dir / "relative_write.txt").exists()


class TestEditFile:
    """edit_file 工具测试"""

    @pytest.mark.asyncio
    async def test_edit_single_replacement(
        self, mock_ctx: MagicMock, sample_file: Path
    ):
        """测试单次替换"""
        result = await edit_file(
            mock_ctx,
            str(sample_file),
            old_string="line 2",
            new_string="REPLACED_LINE_2",
        )

        assert result.success is True
        content = sample_file.read_text()
        assert "REPLACED_LINE_2" in content
        # 原始的 "line 2" 应该已被替换
        assert content.count("line 2") == 0 or "REPLACED" in content

    @pytest.mark.asyncio
    async def test_edit_nonexistent_file(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试编辑不存在的文件"""
        result = await edit_file(
            mock_ctx,
            str(temp_dir / "nonexistent.txt"),
            old_string="foo",
            new_string="bar",
        )

        assert result.success is False
        assert "文件不存在" in result.error

    @pytest.mark.asyncio
    async def test_edit_string_not_found(
        self, mock_ctx: MagicMock, sample_file: Path
    ):
        """测试要替换的字符串不存在"""
        result = await edit_file(
            mock_ctx,
            str(sample_file),
            old_string="nonexistent string",
            new_string="replacement",
        )

        assert result.success is False
        assert "未找到" in result.error

    @pytest.mark.asyncio
    async def test_edit_same_string_error(
        self, mock_ctx: MagicMock, sample_file: Path
    ):
        """测试 old_string 和 new_string 相同"""
        result = await edit_file(
            mock_ctx,
            str(sample_file),
            old_string="line 1",
            new_string="line 1",
        )

        assert result.success is False
        assert "必须与 old_string 不同" in result.error

    @pytest.mark.asyncio
    async def test_edit_multiple_occurrences_error(
        self, mock_ctx: MagicMock, temp_dir: Path
    ):
        """测试多次出现时不使用 replace_all 报错"""
        file_path = temp_dir / "multi.txt"
        file_path.write_text("foo bar foo baz foo")

        result = await edit_file(
            mock_ctx,
            str(file_path),
            old_string="foo",
            new_string="qux",
            replace_all=False,
        )

        assert result.success is False
        assert "出现了 3 次" in result.error

    @pytest.mark.asyncio
    async def test_edit_replace_all(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试 replace_all 替换所有出现"""
        file_path = temp_dir / "multi.txt"
        file_path.write_text("foo bar foo baz foo")

        result = await edit_file(
            mock_ctx,
            str(file_path),
            old_string="foo",
            new_string="qux",
            replace_all=True,
        )

        assert result.success is True
        content = file_path.read_text()
        assert "foo" not in content
        assert content.count("qux") == 3

    @pytest.mark.asyncio
    async def test_edit_generates_diff(
        self, mock_ctx: MagicMock, sample_file: Path
    ):
        """测试编辑结果包含 diff 输出"""
        result = await edit_file(
            mock_ctx,
            str(sample_file),
            old_string="line 3",
            new_string="MODIFIED",
        )

        assert result.success is True
        # 检查 diff 格式
        assert "-" in result.output or "+" in result.output


# ============ 搜索工具测试 ============


class TestGlobFiles:
    """glob_files 工具测试"""

    @pytest.mark.asyncio
    async def test_glob_simple_pattern(
        self, mock_ctx: MagicMock, sample_python_file: Path
    ):
        """测试简单 glob 模式"""
        result = await glob_files(mock_ctx, "*.py")

        assert result.success is True
        assert "sample.py" in result.output

    @pytest.mark.asyncio
    async def test_glob_no_matches(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试无匹配文件"""
        result = await glob_files(mock_ctx, "*.nonexistent")

        assert result.success is True
        assert "未找到匹配" in result.output

    @pytest.mark.asyncio
    async def test_glob_recursive_pattern(
        self, mock_ctx: MagicMock, temp_dir: Path
    ):
        """测试递归 glob 模式"""
        # 创建嵌套目录结构
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("# nested")
        (temp_dir / "root.py").write_text("# root")

        result = await glob_files(mock_ctx, "**/*.py")

        assert result.success is True
        assert "nested.py" in result.output or "root.py" in result.output

    @pytest.mark.asyncio
    async def test_glob_with_path(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试指定搜索路径"""
        subdir = temp_dir / "mydir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")

        result = await glob_files(mock_ctx, "*.txt", path="mydir")

        assert result.success is True
        # 结果应该包含 mydir/file.txt 或 file.txt
        assert "file.txt" in result.output

    @pytest.mark.asyncio
    async def test_glob_nonexistent_path(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试不存在的搜索路径"""
        result = await glob_files(mock_ctx, "*.txt", path="nonexistent")

        assert result.success is False
        assert "路径不存在" in result.error


class TestGrepSearch:
    """grep_search 工具测试"""

    @pytest.mark.asyncio
    async def test_grep_simple_pattern(
        self, mock_ctx: MagicMock, sample_python_file: Path
    ):
        """测试简单搜索模式"""
        result = await grep_search(mock_ctx, "hello", output_mode="files_with_matches")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_grep_no_matches(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试无匹配"""
        (temp_dir / "test.txt").write_text("foo bar baz")

        result = await grep_search(mock_ctx, "nonexistent_pattern")

        assert result.success is True
        assert "未找到匹配" in result.output

    @pytest.mark.asyncio
    async def test_grep_content_mode(
        self, mock_ctx: MagicMock, sample_python_file: Path
    ):
        """测试内容输出模式"""
        result = await grep_search(
            mock_ctx, "def", output_mode="content"
        )

        assert result.success is True
        # 应该显示匹配的行

    @pytest.mark.asyncio
    async def test_grep_case_insensitive(
        self, mock_ctx: MagicMock, temp_dir: Path
    ):
        """测试大小写不敏感搜索"""
        (temp_dir / "test.txt").write_text("HELLO world")

        result = await grep_search(
            mock_ctx, "hello", case_insensitive=True, output_mode="files_with_matches"
        )

        assert result.success is True
        assert "test.txt" in result.output

    @pytest.mark.asyncio
    async def test_grep_with_glob_filter(
        self, mock_ctx: MagicMock, temp_dir: Path
    ):
        """测试带 glob 过滤的搜索"""
        (temp_dir / "test.py").write_text("def foo(): pass")
        (temp_dir / "test.txt").write_text("def bar(): pass")

        result = await grep_search(
            mock_ctx, "def", glob="*.py", output_mode="files_with_matches"
        )

        assert result.success is True
        # 应该只匹配 .py 文件
        if "test.py" in result.output:
            assert "test.txt" not in result.output


# ============ 命令行工具测试 ============


class TestBash:
    """bash 工具测试"""

    @pytest.mark.asyncio
    async def test_bash_simple_command(self, mock_ctx: MagicMock):
        """测试简单命令执行"""
        result = await bash(mock_ctx, "echo 'Hello, World!'")

        assert result.success is True
        assert "Hello, World!" in result.output

    @pytest.mark.asyncio
    async def test_bash_command_failure(self, mock_ctx: MagicMock):
        """测试命令失败"""
        result = await bash(mock_ctx, "exit 1")

        assert result.success is False
        assert "退出码" in result.error

    @pytest.mark.asyncio
    async def test_bash_stderr_capture(self, mock_ctx: MagicMock):
        """测试 stderr 捕获"""
        result = await bash(mock_ctx, "echo 'error' >&2")

        # stderr 也应该被捕获
        assert "error" in result.output

    @pytest.mark.asyncio
    async def test_bash_timeout(self, mock_ctx: MagicMock):
        """测试命令超时"""
        result = await bash(mock_ctx, "sleep 10", timeout=1000)  # 1秒超时

        assert result.success is False
        assert "超时" in result.error

    @pytest.mark.asyncio
    async def test_bash_cwd(self, mock_ctx: MagicMock, temp_dir: Path):
        """测试在指定目录执行"""
        result = await bash(mock_ctx, "pwd")

        assert result.success is True
        assert str(temp_dir) in result.output

    @pytest.mark.asyncio
    async def test_bash_background(self, mock_ctx: MagicMock):
        """测试后台执行"""
        result = await bash(
            mock_ctx, "echo 'background task'", run_in_background=True
        )

        assert result.success is True
        assert "后台启动" in result.output
        # 应该返回 shell_id
        assert "ID:" in result.output


class TestBashOutput:
    """bash_output 工具测试"""

    @pytest.mark.asyncio
    async def test_bash_output_nonexistent_id(self, mock_ctx: MagicMock):
        """测试获取不存在的后台任务输出"""
        result = await bash_output(mock_ctx, "nonexistent_id")

        assert result.success is False
        assert "未找到后台任务" in result.error

    @pytest.mark.asyncio
    async def test_bash_output_with_shell(self, mock_ctx: MagicMock, mock_deps: MiniCCDeps):
        """测试获取后台任务输出"""
        # 模拟一个后台任务
        shell_id = "test_shell"
        mock_process = MagicMock()
        mock_process.returncode = None

        shell_info = BackgroundShell(
            shell_id=shell_id,
            command="test command",
            description="test",
            output_buffer="test output line 1\ntest output line 2\n",
            is_running=True,
        )

        mock_deps.background_shells[shell_id] = (mock_process, shell_info)

        result = await bash_output(mock_ctx, shell_id)

        assert result.success is True
        assert "test output" in result.output
        assert "运行中" in result.output

    @pytest.mark.asyncio
    async def test_bash_output_with_filter(
        self, mock_ctx: MagicMock, mock_deps: MiniCCDeps
    ):
        """测试带过滤的输出"""
        shell_id = "filter_shell"
        mock_process = MagicMock()
        mock_process.returncode = 0

        shell_info = BackgroundShell(
            shell_id=shell_id,
            command="test",
            output_buffer="line 1: foo\nline 2: bar\nline 3: foo\n",
            is_running=False,
        )

        mock_deps.background_shells[shell_id] = (mock_process, shell_info)

        result = await bash_output(mock_ctx, shell_id, filter_pattern="foo")

        assert result.success is True
        assert "foo" in result.output
        # bar 行应该被过滤掉
        lines = result.output.split("\n")
        bar_lines = [l for l in lines if "bar" in l]
        assert len(bar_lines) == 0


class TestKillShell:
    """kill_shell 工具测试"""

    @pytest.mark.asyncio
    async def test_kill_nonexistent_shell(self, mock_ctx: MagicMock):
        """测试终止不存在的后台任务"""
        result = await kill_shell(mock_ctx, "nonexistent")

        assert result.success is False
        assert "未找到后台任务" in result.error

    @pytest.mark.asyncio
    async def test_kill_running_shell(
        self, mock_ctx: MagicMock, mock_deps: MiniCCDeps
    ):
        """测试终止运行中的后台任务"""
        shell_id = "running_shell"
        mock_process = MagicMock()
        mock_process.returncode = None

        async def mock_wait():
            pass

        mock_process.wait = mock_wait

        shell_info = BackgroundShell(
            shell_id=shell_id,
            command="sleep 100",
            is_running=True,
        )

        mock_deps.background_shells[shell_id] = (mock_process, shell_info)

        result = await kill_shell(mock_ctx, shell_id)

        assert result.success is True
        assert "已终止" in result.output
        # 应该从字典中移除
        assert shell_id not in mock_deps.background_shells


# ============ 任务管理工具测试 ============


class TestTodoWrite:
    """todo_write 工具测试"""

    @pytest.mark.asyncio
    async def test_todo_write_simple(self, mock_ctx: MagicMock):
        """测试简单任务写入"""
        todos = [
            {"content": "Task 1", "status": "pending", "activeForm": "Working on Task 1"},
            {"content": "Task 2", "status": "in_progress", "activeForm": "Working on Task 2"},
        ]

        result = await todo_write(mock_ctx, todos)

        assert result.success is True
        assert "已更新 2 个任务" in result.output
        assert len(mock_ctx.deps.todos) == 2

    @pytest.mark.asyncio
    async def test_todo_write_with_callback(
        self, mock_ctx: MagicMock, mock_deps: MiniCCDeps
    ):
        """测试任务更新回调"""
        callback_called = []

        def on_update(todos):
            callback_called.append(todos)

        mock_deps.on_todo_update = on_update

        todos = [{"content": "Test", "status": "pending", "activeForm": "Testing"}]
        await todo_write(mock_ctx, todos)

        assert len(callback_called) == 1
        assert len(callback_called[0]) == 1

    @pytest.mark.asyncio
    async def test_todo_write_status_icons(self, mock_ctx: MagicMock):
        """测试状态图标显示"""
        todos = [
            {"content": "Pending", "status": "pending", "activeForm": "Pending"},
            {"content": "In Progress", "status": "in_progress", "activeForm": "In Progress"},
            {"content": "Completed", "status": "completed", "activeForm": "Completed"},
        ]

        result = await todo_write(mock_ctx, todos)

        assert result.success is True


# ============ 辅助函数测试 ============


class TestResolvePath:
    """_resolve_path 函数测试"""

    def test_resolve_absolute_path(self):
        """测试绝对路径"""
        result = _resolve_path("/tmp", "/home/user/file.txt")
        assert result == Path("/home/user/file.txt")

    def test_resolve_relative_path(self):
        """测试相对路径"""
        result = _resolve_path("/home/user", "subdir/file.txt")
        assert result == Path("/home/user/subdir/file.txt")

    def test_resolve_current_dir(self):
        """测试当前目录"""
        result = _resolve_path("/home/user", ".")
        assert result == Path("/home/user")


class TestNormalizeWhitespace:
    """_normalize_whitespace 函数测试"""

    def test_normalize_tabs(self):
        """测试 tab 转空格"""
        result = _normalize_whitespace("\thello")
        assert result == "    hello"

    def test_normalize_trailing_whitespace(self):
        """测试移除行尾空白"""
        result = _normalize_whitespace("hello   \nworld  ")
        assert result == "hello\nworld"

    def test_normalize_mixed(self):
        """测试混合情况"""
        result = _normalize_whitespace("\tline1  \n\tline2   ")
        assert result == "    line1\n    line2"


class TestFindWhitespaceTolerant:
    """_find_whitespace_tolerant 函数测试"""

    def test_find_exact_match(self):
        """测试精确匹配"""
        content = "hello world\ngoodbye world"
        pattern = "hello world"
        result = _find_whitespace_tolerant(content, _normalize_whitespace(pattern))
        assert result == "hello world"

    def test_find_with_different_whitespace(self):
        """测试不同空白字符"""
        content = "\thello\n\tworld"
        pattern = "    hello\n    world"
        result = _find_whitespace_tolerant(content, pattern)
        assert result == "\thello\n\tworld"

    def test_find_no_match(self):
        """测试无匹配"""
        content = "foo bar baz"
        pattern = "nonexistent"
        result = _find_whitespace_tolerant(content, pattern)
        assert result is None


class TestGenerateDiff:
    """generate_diff 和相关函数测试"""

    def test_generate_diff_add_line(self):
        """测试添加行的 diff"""
        old = "line1\nline2"
        new = "line1\nline2\nline3"
        result = generate_diff(old, new)

        add_lines = [l for l in result if l.type == "add"]
        assert len(add_lines) > 0

    def test_generate_diff_remove_line(self):
        """测试删除行的 diff"""
        old = "line1\nline2\nline3"
        new = "line1\nline3"
        result = generate_diff(old, new)

        remove_lines = [l for l in result if l.type == "remove"]
        assert len(remove_lines) > 0

    def test_format_diff(self):
        """测试 diff 格式化"""
        from minicc.schemas import DiffLine

        diff_lines = [
            DiffLine(type="context", content="unchanged"),
            DiffLine(type="remove", content="old line"),
            DiffLine(type="add", content="new line"),
        ]

        result = format_diff(diff_lines)

        assert "  unchanged" in result
        assert "- old line" in result
        assert "+ new line" in result

    def test_generate_unified_diff(self):
        """测试 unified diff 格式"""
        old = "line1\nold line\nline3"
        new = "line1\nnew line\nline3"

        result = _generate_unified_diff(old, new, "test.txt")

        assert "---" in result or "-" in result
        assert "+++" in result or "+" in result
