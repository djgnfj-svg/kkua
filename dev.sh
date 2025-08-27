#!/bin/bash

echo "🎮 KKUA 개발 환경 시작..."

# Docker Compose로 개발 환경 시작
docker-compose --env-file .env.dev up -d --build

echo "✅ 개발 서버가 시작되었습니다!"
echo "🎯 게임: http://localhost:5173"
echo "📚 API: http://localhost:8000/docs"
echo "❤️  헬스체크: http://localhost:8000/health"
echo ""
echo "로그 확인: docker-compose logs -f"
echo "중지: docker-compose down"