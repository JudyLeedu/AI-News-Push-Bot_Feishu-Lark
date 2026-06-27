"""配置加载模块

配置优先级：环境变量 > config.yaml > 默认值
GitHub Actions 通过 secrets 注入环境变量，无需 config.yaml。
"""
import os
import yaml

_CONFIG = None


def load_config(path: str = None) -> dict:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    if path is None:
        path = os.environ.get("CONFIG_PATH", "config.yaml")

    # 尝试加载 YAML 配置文件
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _CONFIG = yaml.safe_load(f)
    else:
        # GitHub Actions 模式：从环境变量构建配置
        _CONFIG = _build_from_env()

    # 环境变量覆盖（优先级最高）
    _apply_env_overrides(_CONFIG)

    return _CONFIG


def get_config() -> dict:
    if _CONFIG is None:
        return load_config()
    return _CONFIG


def _build_from_env() -> dict:
    """从环境变量构建最小配置（GitHub Actions 模式）"""
    return {
        "feishu": {
            "app_id": os.environ.get("FEISHU_APP_ID", ""),
            "app_secret": os.environ.get("FEISHU_APP_SECRET", ""),
            "recipients": [
                {"email": os.environ.get("FEISHU_RECIPIENT_EMAIL", "")}
            ],
        },
        "llm": {
            "api_base": os.environ.get("LLM_API_BASE", "https://api.openai.com/v1"),
            "api_key": os.environ.get("LLM_API_KEY", ""),
            "model": os.environ.get("LLM_MODEL", "gpt-4o"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "schedule": {
            "timezone": "Asia/Shanghai",
            "daily": {"hour": 8, "minute": 30},
            "weekly": {"day_of_week": "sat", "hour": 8, "minute": 30},
            "monthly": {"day": "last", "hour": 8, "minute": 30},
        },
        "sources": {
            "daily": [],
            "weekly": [],
            "monthly": [],
        },
        "filters": {
            "daily_max_items": 5,
            "weekly_max_items": 1,
            "monthly_max_items": 1,
            "keywords": ["AI", "LLM", "GPT", "Claude", "Gemini", "model", "agent"],
            "exclude_keywords": ["crypto", "NFT", "blockchain"],
        },
        "logging": {"level": "INFO", "file": "logs/bot.log"},
    }


def _apply_env_overrides(config: dict) -> None:
    """环境变量覆盖配置文件中的值"""
    env_map = {
        "FEISHU_APP_ID": ("feishu", "app_id"),
        "FEISHU_APP_SECRET": ("feishu", "app_secret"),
        "FEISHU_RECIPIENT_EMAIL": ("feishu", "recipients", 0, "email"),
        "LLM_API_KEY": ("llm", "api_key"),
        "LLM_API_BASE": ("llm", "api_base"),
        "LLM_MODEL": ("llm", "model"),
    }
    for env_var, path in env_map.items():
        val = os.environ.get(env_var)
        if val:
            target = config
            for key in path[:-1]:
                target = target.setdefault(key, {})
            target[path[-1]] = val
