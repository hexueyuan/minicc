"""
MiniCC 配置管理

处理 ~/.minicc 目录下的配置文件和 AGENTS.md 系统提示词。
"""

import os
from pathlib import Path

from .schemas import Config, Provider


# 配置文件路径
CONFIG_DIR = Path.home() / ".minicc"
CONFIG_FILE = CONFIG_DIR / "config.json"
AGENTS_FILE = CONFIG_DIR / "AGENTS.md"

# 内置系统提示词文件路径
BUILTIN_PROMPT_FILE = Path(__file__).parent / "prompts" / "system.md"


def _load_builtin_prompt() -> str:
    """加载内置系统提示词"""
    if BUILTIN_PROMPT_FILE.exists():
        return BUILTIN_PROMPT_FILE.read_text(encoding="utf-8")
    return "你是一个代码助手，帮助用户完成编程任务。"


def ensure_config_dir() -> None:
    """
    确保配置目录存在

    创建 ~/.minicc 目录（如不存在），并初始化默认配置文件。
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 创建默认配置文件
    if not CONFIG_FILE.exists():
        default_config = Config()
        save_config(default_config)

    # 创建默认 AGENTS.md（从内置提示词复制）
    if not AGENTS_FILE.exists():
        AGENTS_FILE.write_text(_load_builtin_prompt(), encoding="utf-8")


def load_config() -> Config:
    """
    加载应用配置

    从 ~/.minicc/config.json 读取配置，若不存在则返回默认配置。

    Returns:
        Config: 应用配置对象
    """
    ensure_config_dir()

    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text(encoding="utf-8")
        return Config.model_validate_json(content)

    return Config()


def save_config(config: Config) -> None:
    """
    保存应用配置

    将配置写入 ~/.minicc/config.json

    Args:
        config: 要保存的配置对象
    """
    # 只确保目录存在，不调用 ensure_config_dir 避免递归
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        config.model_dump_json(indent=2),
        encoding="utf-8"
    )


def load_agents_prompt() -> str:
    """
    加载系统提示词

    优先级：~/.minicc/AGENTS.md > 内置 prompts/system.md

    Returns:
        str: 系统提示词内容
    """
    ensure_config_dir()

    if AGENTS_FILE.exists():
        return AGENTS_FILE.read_text(encoding="utf-8")

    return _load_builtin_prompt()


def get_api_key(provider: Provider) -> str:
    """
    获取 API 密钥

    优先从配置文件读取，否则从环境变量获取。

    Args:
        provider: LLM 提供商

    Returns:
        str: API 密钥

    Raises:
        ValueError: 未找到 API 密钥时抛出
    """
    config = load_config()

    # 优先使用配置文件中的密钥
    if config.api_key:
        return config.api_key

    # 根据提供商查找环境变量
    env_var_map = {
        Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
        Provider.OPENAI: "OPENAI_API_KEY",
    }

    env_var = env_var_map.get(provider)
    if env_var:
        api_key = os.environ.get(env_var)
        if api_key:
            return api_key

    raise ValueError(
        f"未找到 {provider.value} 的 API 密钥。"
        f"请设置环境变量 {env_var} 或在 ~/.minicc/config.json 中配置 api_key"
    )
