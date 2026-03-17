"""
Alembic env.py — 配置数据库迁移

加载所有 ORM 模型以支持 autogenerate。
"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 将 backend 目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import Base
# 导入所有模型确保 metadata 包含所有表
from app.models.project import Project, ProjectParams  # noqa
from app.models.standard import StdDocument, StdClause, EngCase  # noqa
from app.models.rule import RuleGroup, Rule, RuleCondition, RuleAction  # noqa
from app.models.user import SysUser, SysRole  # noqa
from app.models.mine import SysMine  # noqa
from app.models.document import GeneratedDoc, DocTemplate, ChapterSnippet  # noqa

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
