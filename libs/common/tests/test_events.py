"""Envelope va dinh tuyen event. Khong can RabbitMQ that."""

from __future__ import annotations

import pytest

from common.events import BaseConsumer, EventEnvelope


class FakeProcess:
    """Gia lap message.process(): nem loi ben trong -> reject."""

    def __init__(self, requeue: bool) -> None:
        self.requeue = requeue
        self.rejected = False

    async def __aenter__(self) -> FakeProcess:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.rejected = True
        return False  # cho exception di tiep, giong aio_pika


class FakeMessage:
    def __init__(self, envelope: EventEnvelope) -> None:
        self.body = envelope.to_bytes()
        self.ctx: FakeProcess | None = None

    def process(self, requeue: bool = True) -> FakeProcess:
        self.ctx = FakeProcess(requeue)
        return self.ctx


def make_consumer() -> BaseConsumer:
    return BaseConsumer("amqp://khong-ket-noi", "billing.loan-events", ["loan.*"])


def test_envelope_co_id_va_thoi_diem():
    env = EventEnvelope(type="loan.returned", payload={"loan_id": 5})
    assert len(env.event_id) == 32
    assert env.occurred_at.tzinfo is not None


def test_envelope_roundtrip():
    env = EventEnvelope(type="loan.returned_late", payload={"days_late": 3})
    again = EventEnvelope.from_bytes(env.to_bytes())
    assert again.event_id == env.event_id
    assert again.type == "loan.returned_late"
    assert again.payload == {"days_late": 3}


async def test_dispatch_dung_handler():
    seen: list[EventEnvelope] = []

    async def handler(env: EventEnvelope) -> None:
        seen.append(env)

    consumer = make_consumer()
    consumer.register("loan.returned", handler)
    consumer.register("loan.created", lambda env: pytest.fail("sai handler"))

    message = FakeMessage(EventEnvelope(type="loan.returned", payload={"loan_id": 9}))
    await consumer._on_message(message)  # type: ignore[arg-type]

    assert len(seen) == 1
    assert seen[0].payload == {"loan_id": 9}
    assert message.ctx is not None and message.ctx.rejected is False


async def test_type_khong_co_handler_thi_bo_qua_khong_loi():
    consumer = make_consumer()
    message = FakeMessage(EventEnvelope(type="loan.khong-biet", payload={}))
    await consumer._on_message(message)  # type: ignore[arg-type]
    assert message.ctx is not None and message.ctx.rejected is False


async def test_handler_loi_thi_reject_khong_requeue():
    async def handler(env: EventEnvelope) -> None:
        raise RuntimeError("handler hong")

    consumer = make_consumer()
    consumer.register("loan.returned", handler)

    message = FakeMessage(EventEnvelope(type="loan.returned", payload={}))
    with pytest.raises(RuntimeError):
        await consumer._on_message(message)  # type: ignore[arg-type]

    assert message.ctx is not None
    assert message.ctx.rejected is True
    # requeue=False -> message roi vao DLQ thay vi quay vong vo han.
    assert message.ctx.requeue is False


def test_ten_dlq_theo_ten_queue():
    assert make_consumer().dlq_name == "billing.loan-events.dlq"
