#!/bin/bash

# 끄아(KKUA) 로그 확인 스크립트

ENVIRONMENT=${1:-development}
SERVICE=${2:-}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

if [ -z "$SERVICE" ]; then
    echo "📋 사용 가능한 서비스:"
    docker-compose -f $COMPOSE_FILE ps --services
    echo ""
    echo "사용법: $0 [environment] [service]"
    echo "예시:"
    echo "  $0 development backend  # 개발환경 백엔드 로그"
    echo "  $0 production backend   # 운영환경 백엔드 로그"
    echo "  $0 development          # 모든 서비스 로그"
    exit 0
fi

echo "📖 $ENVIRONMENT 환경의 $SERVICE 로그를 확인합니다..."
docker-compose -f $COMPOSE_FILE logs -f $SERVICE