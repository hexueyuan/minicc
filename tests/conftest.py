"""
MiniCC 测试配置

提供测试 fixtures 和通用工具。
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest

from minicc.schemas import Config, MiniCCDeps, Provider


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录用于测试文件操作"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config() -> Config:
    """创建测试用配置"""
    return Config(
        provider=Provider.ANTHROPIC,
        model="test-model",
        api_key="test-key",
    )


@pytest.fixture
def mock_deps(temp_dir: Path, mock_config: Config) -> MiniCCDeps:
    """创建测试用依赖容器"""
    return MiniCCDeps(
        config=mock_config,
        cwd=str(temp_dir),
        sub_agents={},
        sub_agent_tasks={},
        todos=[],
        background_shells={},
        on_tool_call=None,
        on_todo_update=None,
    )


@pytest.fixture
def mock_ctx(mock_deps: MiniCCDeps) -> MagicMock:
    """创建模拟的 RunContext"""
    ctx = MagicMock()
    ctx.deps = mock_deps
    return ctx


@pytest.fixture
def sample_file(temp_dir: Path) -> Path:
    """创建测试用样本文件"""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("line 1\nline 2\nline 3\nline 4\nline 5\n", encoding="utf-8")
    return file_path


@pytest.fixture
def sample_python_file(temp_dir: Path) -> Path:
    """创建测试用 Python 文件"""
    file_path = temp_dir / "sample.py"
    content = '''"""Sample module"""

def hello():
    """Say hello"""
    print("Hello, World!")

def goodbye():
    """Say goodbye"""
    print("Goodbye!")

class MyClass:
    """A sample class"""
    pass
'''
    file_path.write_text(content, encoding="utf-8")
    return file_path
