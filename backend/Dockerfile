FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir poetry && poetry install --no-root

ARG DATABASE_URL
COPY . .
RUN poetry run alembic upgrade head

EXPOSE 8000
CMD ["poetry", "run", "prod"]