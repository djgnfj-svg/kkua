#!/bin/bash

# 끄아(KKUA) 간단 배포 스크립트

echo "🚀 끄아 게임 배포 시작..."

# Docker 이미지 및 컨테이너 정리
echo "🧹 기존 Docker 환경 정리..."
docker-compose down --volumes --remove-orphans 2>/dev/null || true
docker system prune -af --volumes 2>/dev/null || true

# 프로덕션 환경 구성
echo "🏗️  프로덕션 환경 빌드 시작..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 서비스 시작
echo "🎮 서비스 시작..."
docker-compose -f docker-compose.prod.yml up -d

# 헬스 체크
echo "🔍 서비스 상태 확인 중..."
sleep 10

if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "✅ 배포 완료!"
    echo "🌐 프론트엔드: http://localhost"
    echo "🔧 백엔드 API: http://localhost/api"
    echo "📊 로그 확인: docker-compose -f docker-compose.prod.yml logs -f"
else
    echo "❌ 배포 실패. 로그를 확인하세요:"
    docker-compose -f docker-compose.prod.yml logs --tail=50
    exit 1
fi