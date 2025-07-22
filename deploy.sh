#!/bin/bash

# =======================================================================
# 끄아 (KKUA) - 간단한 Docker 배포 스크립트
# =======================================================================

set -e

echo "🚀 끄아 배포를 시작합니다..."

# 환경 설정
ENVIRONMENT=${1:-development}
echo "📁 환경: $ENVIRONMENT"

# .env 파일 확인 및 생성
if [ ! -f "backend/.env" ]; then
    echo "💡 .env 파일을 생성합니다..."
    cp backend/.env.example backend/.env
fi

# Docker 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    exit 1
fi

# 배포 실행
echo "🛑 기존 서비스를 중지합니다..."
docker-compose down --remove-orphans 2>/dev/null || true

echo "🔨 이미지를 빌드합니다..."
docker-compose build

echo "🚀 서비스를 시작합니다..."
if [ "$ENVIRONMENT" = "production" ]; then
    ENVIRONMENT=production docker-compose up -d --profile frontend
else
    docker-compose up -d --profile frontend
fi

# 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 10

echo "🔍 서비스 상태 확인:"
docker-compose ps

echo ""
echo "🎉 배포 완료!"
echo "🌐 서비스 URL:"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "   백엔드: http://localhost:8000"
else
    echo "   프론트엔드: http://localhost:3000"
    echo "   백엔드: http://localhost:8000"
fi
echo ""
echo "📋 명령어:"
echo "   로그: docker-compose logs -f"
echo "   중지: docker-compose down"
echo ""