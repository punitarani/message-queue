"""api.py"""

import json
from contextlib import asynccontextmanager

import aio_pika
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from mq.config import get_rabbitmq_url
from mq.db import AsyncSessionLocal, engine
from mq.models import Base, Order
from mq.schemas import OrderResponse, OrderStatusResponse

RABBITMQ_URL = get_rabbitmq_url()


async def get_db():
    """Get the database session"""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.channel = await app.state.rabbitmq_connection.channel()
    # Ensure the queue exists
    app.state.queue = await app.state.channel.declare_queue("order_queue", durable=True)

    yield
    await app.state.channel.close()
    await app.state.rabbitmq_connection.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    health_status = {"status": "healthy", "database": "healthy", "rabbitmq": "healthy"}

    # Check database connection
    try:
        await db.execute("SELECT 1")
    except SQLAlchemyError:
        health_status["database"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Check RabbitMQ connection
    if not app.state.rabbitmq_connection.is_closed:
        try:
            await app.state.channel.declare_queue("health_check", passive=True)
        except Exception:
            health_status["rabbitmq"] = "unhealthy"
            health_status["status"] = "unhealthy"
    else:
        health_status["rabbitmq"] = "unhealthy"
        health_status["status"] = "unhealthy"

    return health_status


@app.post("/order/place", response_model=OrderResponse)
async def place_order(db: AsyncSession = Depends(get_db)):
    new_order = Order()
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    order_id = new_order.id

    message = aio_pika.Message(
        body=json.dumps({"order_id": order_id}).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await app.state.channel.default_exchange.publish(message, routing_key="order_queue")
    return OrderResponse(order_id=order_id, status=new_order.status)


@app.get("/order/get/{order_id}", response_model=OrderStatusResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderStatusResponse(order_id=order.id, status=order.status)


@app.get("/debug/orders", response_model=list[OrderStatusResponse])
async def get_all_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order))
    orders = result.scalars().all()
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")
    return [
        OrderStatusResponse(order_id=order.id, status=order.status) for order in orders
    ]
