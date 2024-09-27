"""config.py"""

import os


def get_db_url():
    """Get the Postgres database URL."""
    return os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://user:password@postgres:5432/db"
    )


def get_rabbitmq_url():
    """Get the RabbitMQ URL."""
    return os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
