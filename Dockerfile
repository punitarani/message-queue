# Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-dev

COPY mq/ /app/mq/

CMD ["sh", "-c", "uvicorn mq.api:app --host 0.0.0.0 --port ${PORT:-3000}"]
