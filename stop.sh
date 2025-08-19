#!/bin/bash

# 끄아(KKUA) 게임 중지 스크립트

set -e

ENVIRONMENT=${1:-development}

echo "🛑 끄아(KKUA) 서비스를 중지합니다..."
echo "📁 환경: $ENVIRONMENT"

# 모든 서비스 중지 및 컨테이너 제거
docker-compose down

echo "✅ 모든 서비스가 중지되었습니다."

# 옵션: 데이터도 함께 삭제 (주의!)
if [ "$2" = "--with-data" ]; then
    echo "⚠️  데이터 볼륨도 삭제합니다..."
    docker-compose down -v
    echo "🗑️  모든 데이터가 삭제되었습니다."
fi