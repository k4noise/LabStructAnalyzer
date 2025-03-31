FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir poetry && poetry install --no-root

COPY . .
RUN poetry run alembic upgrade head

EXPOSE 8000
CMD ["poetry", "run", "prod"]