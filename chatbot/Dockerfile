FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# 소스 코드를 src 디렉토리로 복사
COPY src/ src/

# 데이터 디렉토리 구조 생성
RUN mkdir -p /app/src/data/static \
    && mkdir -p /app/src/data/dynamic/logs \
    && chmod -R 777 /app/src/data/dynamic

# 정적 데이터 파일 복사 (JSON 파일들)
COPY src/data/static/ src/data/static/

# Python 모듈 경로 설정
ENV PYTHONPATH=/app:/app/api

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]