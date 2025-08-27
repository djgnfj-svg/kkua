#!/bin/bash

# 끄아(KKUA) 프로덕션 배포 스크립트

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 끄아 게임 프로덕션 배포 시작..."

# 프로덕션 환경 변수 파일 확인
if [ ! -f .env.prod ]; then
    echo "⚠️  .env.prod 파일이 없습니다. .env.prod 파일을 생성하고 설정을 확인하세요."
    exit 1
fi

# .env 파일 생성 (프로덕션 설정 복사)
cp .env.prod .env

# 보안 키 확인
if grep -q "실제-보안-키로-변경\|your-secret-key\|your-jwt-secret" .env; then
    echo "⚠️  보안 키를 실제 값으로 변경해야 합니다!"
    echo "📝 .env 파일에서 SECRET_KEY와 JWT_SECRET을 수정하세요."
    exit 1
fi

# Docker 이미지 및 컨테이너 정리
echo "🧹 기존 Docker 환경 정리..."
docker-compose --profile production down --volumes --remove-orphans 2>/dev/null || true
docker system prune -f 2>/dev/null || true

# 프로덕션 환경 구성
echo "🏗️  프로덕션 환경 빌드 시작..."
docker-compose --profile production build --no-cache

# 서비스 시작 (프로덕션 프로필 포함)
echo "🎮 서비스 시작..."
docker-compose --profile production up -d

# 서비스 시작 대기
echo "⏳ 서비스 초기화 대기 중 (60초)..."
sleep 60

# 헬스 체크
echo "🔍 서비스 상태 확인 중..."
if docker-compose --profile production ps | grep -q "Up"; then
    echo "✅ 배포 완료!"
    echo "🌐 프론트엔드: http://localhost"
    echo "🔧 백엔드 API: http://localhost/api"
    echo "❤️  헬스체크: http://localhost/health"
    echo ""
    echo "📊 유용한 명령어:"
    echo "   로그 확인: docker-compose --profile production logs -f"
    echo "   서비스 상태: docker-compose --profile production ps"
    echo "   서비스 중지: docker-compose --profile production down"
else
    echo "❌ 배포 실패. 로그를 확인하세요:"
    docker-compose --profile production logs --tail=50
    exit 1
fi