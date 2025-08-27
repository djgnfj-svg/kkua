#!/bin/bash

# KKUA 개발 환경 시작 스크립트

echo "🚀 끄아 개발 환경 시작..."

# 개발 환경 설정 로드 및 시작
docker-compose --env-file .env.dev up -d

echo "✅ 개발 환경이 시작되었습니다!"
echo ""
echo "🌐 접속 주소:"
echo "   프론트엔드: http://localhost:5173"
echo "   백엔드 API: http://localhost:8000"
echo "   API 문서: http://localhost:8000/docs"
echo ""
echo "📊 유용한 명령어:"
echo "   로그 보기: docker-compose --env-file .env.dev logs -f"
echo "   상태 확인: docker-compose --env-file .env.dev ps"
echo "   서비스 중지: docker-compose --env-file .env.dev down"