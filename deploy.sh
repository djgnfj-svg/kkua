#!/bin/bash

echo "🚀 KKUA 프로덕션 배포 시작..."

# 환경 변수 파일 확인
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod 파일이 없습니다!"
    exit 1
fi

# Docker Compose로 프로덕션 환경 시작
docker-compose --env-file .env.prod up -d --build

echo "✅ 프로덕션 서버가 시작되었습니다!"
echo "🎯 게임: http://localhost (port 80)"
echo "📚 API: http://localhost/api/docs"
echo ""
echo "로그 확인: docker-compose logs -f"
echo "중지: docker-compose down"