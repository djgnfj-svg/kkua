#!/bin/bash

echo "🚀 KKUA 프로덕션 환경 시작..."

# Docker Compose로 프로덕션 환경 시작
docker-compose --env-file .env.prod up -d --build

echo "✅ 프로덕션 서버가 시작되었습니다!"
echo "🌐 웹사이트: http://localhost:80"
echo "📚 API: http://localhost:80/api"
echo ""
echo "로그 확인: docker-compose --env-file .env.prod logs -f"
echo "중지: docker-compose --env-file .env.prod down"