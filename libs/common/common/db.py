"""Engine, session va Base dung chung.

Ca 5 service noi vao MOT database `library_db` (quyet dinh cua chu du an:
schema MySQL 20 bang da co san). Vi vay engine, MetaData va Base nam o day
thay vi lap lai trong tung service.

Ranh gioi giua cac service la QUY UOC, khong duoc DB ep buoc: moi service
chi khai bao model cho bang no so huu. Test tests/test_table_ownership.py
trong libs/common canh gac dieu do.

Schema do db/*.sql quan ly - khong dung Alembic, va khong dung
metadata.create_all() ngoai moi truong test.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Ten constraint on dinh -> so sanh model voi schema that de doan hon.
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class CreatedAtMixin:
    """Cho bang chi co created_at (roles, authors, shelves, payments...)."""

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TimestampMixin(CreatedAtMixin):
    """Cho bang co ca created_at va updated_at.

    Cot la DATETIME (khong timezone) dung nhu schema. Schema khong khai bao
    ON UPDATE CURRENT_TIMESTAMP nen onupdate o tang ORM la thu bump gia tri.
    """

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def configure_database(url: str, *, echo: bool = False) -> AsyncEngine:
    """Tao engine. Goi trong lifespan cua moi service. Goi lai la no-op."""
    global _engine, _session_factory
    if _engine is not None:
        return _engine

    _engine = create_async_engine(
        url,
        echo=echo,
        pool_size=10,
        max_overflow=5,
        pool_pre_ping=True,
        # MySQL dong connection nhan roi sau wait_timeout (mac dinh 8 tieng);
        # khong co pool_recycle thi gap loi "server has gone away".
        pool_recycle=3600,
        # Ca he thong lam viec bang UTC. DATETIME cua MySQL khong luu offset
        # nen phai ep session ve UTC, neu khong NOW() se theo gio may chu.
        connect_args={"init_command": "SET time_zone = '+00:00'"},
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_engine() -> AsyncEngine:
    if _engine is None:
        # Du phong cho test/script chay ngoai lifespan.
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("Chua goi configure_database() va khong co DATABASE_URL")
        return configure_database(url)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency FastAPI: moi request mot session rieng.

    Khong commit o day - transaction do tang service quan ly.
    """
    async with get_session_factory()() as session:
        yield session


async def dispose_database() -> None:
    """Dong engine khi service tat."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
