#!/bin/bash

echo "🚀 KKUA 프로덕션 배포 시작..."

# 환경 변수 파일 확인
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod 파일이 없습니다!"
    echo "💡 .env.prod를 생성하고 도메인 설정을 완료하세요."
    exit 1
fi

# .env.prod의 도메인 설정 확인
if grep -q "your-domain.com" .env.prod; then
    echo "❌ .env.prod에서 도메인을 실제 값으로 변경하세요!"
    echo "   - CORS_ORIGINS"
    echo "   - VITE_API_URL"
    echo "   - VITE_WS_URL"
    exit 1
fi

# 보안 키 확인
if grep -q "your-secure-postgres-password-change-me" .env.prod; then
    echo "❌ .env.prod에서 데이터베이스 비밀번호를 변경하세요!"
    exit 1
fi

# Docker Compose로 프로덕션 환경 시작
echo "📦 프로덕션 컨테이너 빌드 및 시작 중..."
docker-compose --env-file .env.prod up -d --build

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 헬스체크
if curl -s http://localhost/health > /dev/null; then
    echo "✅ 프로덕션 서버가 성공적으로 시작되었습니다!"
    echo ""
    echo "📊 서비스 URL:"
    echo "   🎮 게임: http://localhost"
    echo "   📚 API: http://localhost/api/docs"
    echo "   ❤️  헬스체크: http://localhost/health"
    echo ""
    echo "🔧 관리 명령어:"
    echo "   로그 확인: docker-compose --env-file .env.prod logs -f"
    echo "   서비스 중지: docker-compose --env-file .env.prod down"
    echo "   컨테이너 상태: docker-compose --env-file .env.prod ps"
else
    echo "❌ 서비스 시작에 실패했습니다. 로그를 확인하세요:"
    echo "   docker-compose --env-file .env.prod logs"
fi