#!/bin/bash

# 끄아(KKUA) 서비스 상태 확인 스크립트

ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "📊 끄아(KKUA) 서비스 상태 - $ENVIRONMENT 환경"
echo "==============================================="

# Docker Compose 서비스 상태
echo "🐳 Docker 컨테이너 상태:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "💾 Docker 볼륨 상태:"
docker volume ls | grep kkua || echo "볼륨 없음"

echo ""
echo "🌐 네트워크 연결 테스트:"

# 백엔드 헬스 체크
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 백엔드: http://localhost:8000 (정상)"
else
    echo "❌ 백엔드: http://localhost:8000 (연결 실패)"
fi

# 프론트엔드 체크 (개발 환경만)
if [ "$ENVIRONMENT" != "production" ]; then
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ 프론트엔드: http://localhost:3000 (정상)"
    else
        echo "❌ 프론트엔드: http://localhost:3000 (연결 실패)"
    fi
fi

echo ""
echo "📈 리소스 사용량:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep kkua || echo "실행 중인 컨테이너 없음"