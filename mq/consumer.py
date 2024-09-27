"""consumer.py"""

import asyncio
import json
import logging
import random

import aio_pika
from sqlalchemy.future import select

from mq.config import get_rabbitmq_url
from mq.db import AsyncSessionLocal
from mq.models import Order

RABBITMQ_URL = get_rabbitmq_url()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def process_order(message: aio_pika.IncomingMessage):
    async with message.process():
        order_data = json.loads(message.body)
        order_id = order_data["order_id"]
        logging.info(f"Processing order {order_id}")

        async with AsyncSessionLocal() as session:
            # Fetch the order
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalars().first()
            if not order:
                # Order not found
                return

            # Update status to 'processing'
            order.status = "processing"
            await session.commit()
            logging.info(f"Order {order_id} status updated to 'processing'")

            # Simulate processing time between 10ms and 10s
            processing_time = random.uniform(0.01, 10)
            await asyncio.sleep(processing_time)

            # Update status to 'done'
            order.status = "done"
            await session.commit()
            logging.info(
                f"Order {order_id} processing completed. Status updated to 'done'"
            )


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    # Ensure the queue exists
    queue = await channel.declare_queue("order_queue", durable=True)

    # Create a semaphore to limit concurrent consumers to 20
    semaphore = asyncio.Semaphore(20)

    async def consumer_wrapper(message):
        async with semaphore:
            await process_order(message)

    await queue.consume(consumer_wrapper)
    logging.info("Consumer started and waiting for messages")
    try:
        await asyncio.Future()  # Keep the consumer running
    finally:
        await channel.close()
        await connection.close()
        logging.info("Consumer stopped")


if __name__ == "__main__":
    asyncio.run(main())
