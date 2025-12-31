"""
MiniCC 日志模块

提供会话日志记录功能，每次会话在 ~/.minicc/log 下创建独立的会话目录。
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path


class Logger:
    """
    会话日志记录器

    Args:
        session_id: 会话唯一标识
    """

    # 日志根目录（类级别）
    LOG_DIR = Path.home() / ".minicc" / "log"
    LOG_FILE_NAME = "minicc-app.log"

    def __init__(self, session_id: str) -> None:
        """初始化日志会话"""
        self._session_id = session_id
        self._session_dir: Path | None = None
        self._log_file: Path | None = None
        self._lock = threading.Lock()
        self._init_session()

    def _init_session(self) -> None:
        """初始化会话日志目录和文件"""
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        # 使用传入的 session_id 创建会话目录
        self._session_dir = self.LOG_DIR / self._session_id
        self._session_dir.mkdir(parents=True, exist_ok=True)

        self._log_file = self._session_dir / self.LOG_FILE_NAME

    @property
    def session_id(self) -> str:
        """获取会话 ID"""
        return self._session_id

    @property
    def log_file(self) -> Path | None:
        """获取当前会话的日志文件路径"""
        return self._log_file

    @property
    def session_dir(self) -> Path | None:
        """获取当前会话目录路径"""
        return self._session_dir

    def print(self, message: str) -> None:
        """
        写入日志消息

        Args:
            message: 要写入的日志消息
        """
        if self._log_file is None:
            return

        # 获取当前时间
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # 格式化日志行
        log_line = f"[{timestamp}] {message}\n"

        # 追加写入日志文件
        with self._lock:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
