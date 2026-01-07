from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 数据库配置
    db_server: str = "localhost"
    db_database: str = "NationalParkDB"
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_trusted_connection: bool = True
    db_trust_server_cert: bool = True

    # 应用配置
    app_secret_key: str = "change-me-to-a-secure-random-key-32-chars"
    session_idle_minutes: int = 30
    login_fail_limit: int = 5  # 登录失败次数限制

    # CORS配置
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"]

    # 备份配置
    backup_path: str = "./backups"
    backup_interval_hours: int = 24  # 每日备份

    # 设备配置
    device_check_interval: int = 3600  # 设备状态检查间隔（秒）

    # 数据监控阈值
    data_quality_threshold: float = 0.95  # 数据质量阈值
    abnormal_data_retention_days: int = 30  # 异常数据保留天数

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()