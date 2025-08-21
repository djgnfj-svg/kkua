# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# 빌드 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 가상환경 생성 및 Python 의존성 설치
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 가상환경 복사
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 비특권 사용자 생성
RUN groupadd -r kkua && useradd -r -g kkua kkua

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 코드 복사 (실제 존재하는 파일들만)
COPY --chown=kkua:kkua main.py .
COPY --chown=kkua:kkua auth.py .
COPY --chown=kkua:kkua database.py .
COPY --chown=kkua:kkua redis_models.py .
COPY --chown=kkua:kkua database_schema.sql .
COPY --chown=kkua:kkua models/ ./models/
COPY --chown=kkua:kkua services/ ./services/
COPY --chown=kkua:kkua websocket/ ./websocket/

# 로그 디렉토리 생성
RUN mkdir -p /app/logs && chown -R kkua:kkua /app/logs

# 헬스체크 스크립트 추가
COPY --chown=kkua:kkua scripts/healthcheck.py ./scripts/
RUN chmod +x ./scripts/healthcheck.py

# 사용자 전환
USER kkua

# 포트 노출
EXPOSE 8000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python scripts/healthcheck.py || exit 1

# 환경별 실행 명령
ARG ENVIRONMENT=development
ENV ENVIRONMENT=${ENVIRONMENT}

# Production에서는 multi-worker, development에서는 reload
CMD if [ "$ENVIRONMENT" = "production" ]; then \
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4; \
    else \
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload; \
    fi