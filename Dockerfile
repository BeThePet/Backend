FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY . .

ENV PYTHONPATH=/app/api

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]