"""全局配置模块。

配置读取优先级（从高到低）：
1. 系统环境变量（推荐用于敏感信息，如 DEEPSEEK_API_KEY、DB_PASSWORD）
2. 项目根目录 .env 文件（仅本地开发兜底，已加入 .gitignore，禁止提交）
3. 字段默认值
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "安心保"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8001

    # 日志配置
    logging_level: str = "INFO"

    # 数据库配置
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "insurance"
    db_user: str = "insurance"
    db_password: str

    # 模型配置
    deepseek_api_key: str
    chat_model: str = "deepseek-v4-flash"


@lru_cache
def get_settings() -> Settings:
    """获取全局唯一的配置实例。

    若 DEEPSEEK_API_KEY / DB_PASSWORD 未在任何环境变量或 .env 中设置，
    启动时会直接抛出 ValidationError，实现 fail-fast，避免带着空密钥运行。
    """
    return Settings()
