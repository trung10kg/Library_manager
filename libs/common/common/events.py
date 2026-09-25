"""Event qua RabbitMQ.

Exchange `library.events` loai topic, routing key chinh la `type` cua event.
Moi consumer co queue rieng (vd `billing.loan-events`).

Hai quy tac bat buoc:
  - Chi publish SAU KHI commit thanh cong.
  - Consumer phai luu event_id vao bang processed_events TRONG CUNG
    transaction voi thay doi nghiep vu, de RabbitMQ gui lai cung khong
    phat trung.

Handler nem exception thi message bi reject khong requeue va roi vao
dead-letter queue `<queue>.dlq`, thay vi quay vong vo han.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

import aio_pika
from aio_pika.abc import AbstractExchange, AbstractRobustConnection
from pydantic import BaseModel, Field

from common.datetime_utils import utc_now

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "library.events"

Handler = Callable[["EventEnvelope"], Awaitable[None]]


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    type: str
    occurred_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_bytes(self) -> bytes:
        return self.model_dump_json().encode("utf-8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> EventEnvelope:
        return cls.model_validate_json(raw.decode("utf-8"))


class EventPublisher:
    def __init__(self, url: str, exchange_name: str = EXCHANGE_NAME) -> None:
        self.url = url
        self.exchange_name = exchange_name
        self._conn: AbstractRobustConnection | None = None
        self._exchange: AbstractExchange | None = None

    async def connect(self) -> None:
        self._conn = await aio_pika.connect_robust(self.url)
        channel = await self._conn.channel()
        self._exchange = await channel.declare_exchange(
            self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish(self, type_: str, payload: dict[str, Any]) -> EventEnvelope:
        if self._exchange is None:
            raise RuntimeError("Chua goi connect()")
        envelope = EventEnvelope(type=type_, payload=payload)
        await self._exchange.publish(
            aio_pika.Message(
                body=envelope.to_bytes(),
                content_type="application/json",
                message_id=envelope.event_id,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=type_,
        )
        logger.info("Da publish %s (%s)", type_, envelope.event_id)
        return envelope

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
        self._conn = None
        self._exchange = None


class BaseConsumer:
    """Consumer co queue rieng + dead-letter queue."""

    def __init__(
        self,
        url: str,
        queue_name: str,
        routing_keys: list[str],
        exchange_name: str = EXCHANGE_NAME,
        prefetch: int = 10,
    ) -> None:
        self.url = url
        self.queue_name = queue_name
        self.dlq_name = f"{queue_name}.dlq"
        self.routing_keys = routing_keys
        self.exchange_name = exchange_name
        self.prefetch = prefetch
        self._handlers: dict[str, Handler] = {}
        self._conn: AbstractRobustConnection | None = None

    def register(self, type_: str, handler: Handler) -> None:
        self._handlers[type_] = handler

    async def start(self) -> None:
        self._conn = await aio_pika.connect_robust(self.url)
        channel = await self._conn.channel()
        await channel.set_qos(prefetch_count=self.prefetch)

        exchange = await channel.declare_exchange(
            self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        # Message bi reject se di qua default exchange toi queue .dlq.
        await channel.declare_queue(self.dlq_name, durable=True)
        queue = await channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": self.dlq_name,
            },
        )
        for key in self.routing_keys:
            await queue.bind(exchange, routing_key=key)

        await queue.consume(self._on_message)
        logger.info("Consumer %s dang nghe %s", self.queue_name, self.routing_keys)

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        # requeue=False: loi thi vao DLQ, khong quay vong.
        async with message.process(requeue=False):
            envelope = EventEnvelope.from_bytes(message.body)
            handler = self._handlers.get(envelope.type)
            if handler is None:
                logger.warning(
                    "%s: khong co handler cho %s, bo qua", self.queue_name, envelope.type
                )
                return
            await handler(envelope)

    async def stop(self) -> None:
        if self._conn is not None:
            await self._conn.close()
        self._conn = None
