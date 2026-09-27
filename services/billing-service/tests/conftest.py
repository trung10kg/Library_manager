from __future__ import annotations

import os
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from common.testing import generate_rsa_keypair

_PRIVATE_KEY, _PUBLIC_KEY = generate_rsa_keypair()

# Phai dat TRUOC khi import app: Settings doc env ngay luc khoi tao.
os.environ["JWT_PUBLIC_KEY"] = _PUBLIC_KEY
os.environ.pop("JWT_PUBLIC_KEY_PATH", None)
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+aiomysql://root:1234@127.0.0.1:3306/library_test_db?charset=utf8mb4",
)
os.environ.setdefault("SCHEMA_DIR", str(Path(__file__).resolve().parents[3] / "db"))

from tests.seed_ids import (  # noqa: E402
    ADMIN_ID,
    CLEAN_READER_ID,
    LIBRARIAN_ID,
    READER_ID,
    READER_USER_ID,
)

from app.main import create_app  # noqa: E402
from app.models import Fine, FineStatus, FineType  # noqa: E402
from common.db import get_session  # noqa: E402
from common.security import Role  # noqa: E402
from common.testing import (  # noqa: E402
    create_test_engine,
    load_schema,
    make_token,
    rollback_session,
)

DATABASE_URL = os.environ["DATABASE_URL"]


def _client_for(app) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    )


# --- Khoa & DB --------------------------------------------------------------


@pytest.fixture(scope="session")
def private_key() -> str:
    return _PRIVATE_KEY


@pytest.fixture(scope="session")
def schema() -> None:
    """Dung lai library_test_db tu db/*.sql, mot lan cho ca phien."""
    load_schema(DATABASE_URL)


@pytest.fixture(scope="session")
async def engine(schema: None) -> AsyncIterator[AsyncEngine]:
    eng = create_test_engine(DATABASE_URL)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Moi test mot session tu hoan tac - DB sach cho test sau."""
    async with rollback_session(engine) as s:
        yield s


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Client dung chung session voi test: test thay ngay du lieu request ghi."""
    app = create_app()

    async def _override() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _override
    async with _client_for(app) as c:
        yield c


# --- Token ------------------------------------------------------------------


@pytest.fixture
def headers(private_key: str) -> Callable[..., dict[str, str]]:
    def _headers(
        roles: Iterable[Role] = (Role.LIBRARIAN,),
        *,
        user_id: int | None = None,
        reader_id: int | None = None,
    ) -> dict[str, str]:
        roles = list(roles)
        if user_id is None:
            user_id = ADMIN_ID if Role.ADMIN in roles else LIBRARIAN_ID
        token = make_token(private_key, user_id=user_id, roles=roles, reader_id=reader_id)
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.fixture
def staff(headers) -> dict[str, str]:
    return headers([Role.LIBRARIAN])


@pytest.fixture
def admin(headers) -> dict[str, str]:
    return headers([Role.ADMIN])


@pytest.fixture
def reader(headers) -> dict[str, str]:
    """docgia01, reader_id = 1."""
    return headers([Role.READER], user_id=READER_USER_ID, reader_id=READER_ID)


# --- Du lieu ------------------------------------------------------------------


@pytest.fixture
def make_fine(session: AsyncSession) -> Callable[..., Awaitable[Fine]]:
    async def _make(
        *,
        reader_id: int = CLEAN_READER_ID,
        amount: str = "50000.00",
        fine_type: FineType = FineType.DAMAGE,
        status: FineStatus = FineStatus.UNPAID,
        notes: str | None = None,
    ) -> Fine:
        fine = Fine(
            reader_id=reader_id,
            fine_type=fine_type,
            amount=Decimal(amount),
            status=status,
            notes=notes,
        )
        session.add(fine)
        await session.flush()
        return fine

    return _make


# --- Test race: connection that, commit that ----------------------------------


@dataclass
class RealEnv:
    """Moi request mot session rieng va commit that - nhu khi chay that.

    Dung cho test hai request song song; savepoint khong chia se giua cac
    connection nen khong dung duoc rollback_session. Tu xoa khoan phat da tao
    (payments xoa theo FK CASCADE).
    """

    client: AsyncClient
    factory: async_sessionmaker[AsyncSession]
    fine_ids: list[int] = field(default_factory=list)

    async def create_fine(self, amount: str) -> Fine:
        async with self.factory() as s:
            fine = Fine(
                reader_id=CLEAN_READER_ID,
                fine_type=FineType.DAMAGE,
                amount=Decimal(amount),
                status=FineStatus.UNPAID,
            )
            s.add(fine)
            await s.commit()
        self.fine_ids.append(fine.id)
        return fine


@pytest.fixture
async def real_env(engine: AsyncEngine) -> AsyncIterator[RealEnv]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    app = create_app()

    async def _override() -> AsyncIterator[AsyncSession]:
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override
    async with _client_for(app) as c:
        env = RealEnv(client=c, factory=factory)
        yield env

    if env.fine_ids:
        async with factory() as s:
            await s.execute(delete(Fine).where(Fine.id.in_(env.fine_ids)))
            await s.commit()
