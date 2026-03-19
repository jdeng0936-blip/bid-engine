"""
Alembic 迁移环境配置 — 支持 asyncpg 异步引擎
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Alembic Config 对象
config = context.config

# 日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------- 动态注入 DATABASE_URL ----------
from app.core.config import settings

# 将 asyncpg URL 注入到 alembic config（替代 alembic.ini 里的硬编码）
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ---------- 导入所有模型的 metadata ----------
from app.models.base import Base  # noqa: E402

# 确保所有模型已被 import（注册到 Base.metadata）
import app.models.user        # noqa: F401
import app.models.project     # noqa: F401
import app.models.standard    # noqa: F401
import app.models.rule        # noqa: F401
import app.models.document    # noqa: F401
import app.models.feedback    # noqa: F401
import app.models.audit_log   # noqa: F401
import app.models.mine        # noqa: F401
import app.models.drawing     # noqa: F401
import app.models.dict_item   # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：只生成 SQL 脚本"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """实际执行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # 检测字段类型变更
        compare_server_default=True,  # 检测默认值变更
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式：通过 asyncpg 连接数据库"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式：创建异步引擎并执行迁移"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
