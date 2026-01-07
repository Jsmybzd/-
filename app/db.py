from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pyodbc
import urllib.parse

from app.config import settings

# 定义Base类
Base = declarative_base()


def _select_sqlserver_driver() -> str:
    installed = set(pyodbc.drivers())
    if settings.db_driver in installed:
        return settings.db_driver

    for d in [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server",
    ]:
        if d in installed:
            return d

    raise RuntimeError(f"No usable SQL Server ODBC driver found. Installed drivers: {sorted(installed)}")


_SQLSERVER_DRIVER = _select_sqlserver_driver()


def _build_odbc_conn_str() -> str:
    parts = [
        f"DRIVER={{{_SQLSERVER_DRIVER}}}",
        f"SERVER={settings.db_server}",
        f"DATABASE={settings.db_database}",
    ]

    if settings.db_trusted_connection:
        parts.append("Trusted_Connection=yes")

    if settings.db_trust_server_cert:
        parts.append("TrustServerCertificate=yes")

    parts.append("Encrypt=yes")

    return ";".join(parts)


engine = create_engine(
    "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(_build_odbc_conn_str()),
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()