#!/bin/bash

echo "🚀 KKUA 프로덕션 배포 시작..."

# 환경 변수 파일 확인
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod 파일이 없습니다!"
    echo "💡 .env.prod를 생성하고 도메인 설정을 완료하세요."
    exit 1
fi

# 도메인 입력 받기
DOMAIN=""

# 명령행 인수로 도메인이 제공되었는지 확인
if [ $# -gt 0 ]; then
    DOMAIN="$1"
    echo "🌐 사용할 도메인: $DOMAIN"
else
    # .env.prod의 도메인 설정 확인 (your-domain.com인 경우만)
    if grep -q "your-domain.com" .env.prod; then
        echo "⚠️  도메인을 입력하거나 선택하세요:"
        echo ""
        echo "1. localhost (로컬 테스트용)"
        echo "2. 커스텀 도메인 입력"
        echo ""
        read -p "선택하세요 (1/2): " -n 1 -r choice
        echo
        
        if [[ $choice == "1" ]]; then
            DOMAIN="localhost"
        elif [[ $choice == "2" ]]; then
            read -p "🌐 도메인을 입력하세요 (예: mydomain.com): " DOMAIN
            if [ -z "$DOMAIN" ]; then
                echo "❌ 도메인을 입력하지 않았습니다."
                exit 1
            fi
        else
            echo "❌ 잘못된 선택입니다."
            exit 1
        fi
    else
        echo "✅ 도메인이 이미 설정되어 있습니다."
        DOMAIN_CHECK=$(grep "CORS_ORIGINS=" .env.prod | cut -d'=' -f2 | sed 's|https\?://||' | sed 's|wss\?://||')
        DOMAIN="$DOMAIN_CHECK"
    fi
fi

# 도메인 설정 적용 (your-domain.com인 경우만)
if grep -q "your-domain.com" .env.prod; then
    echo "🔧 도메인을 '$DOMAIN'으로 설정 중..."
    
    # 도메인 변경
    sed -i "s/your-domain.com/$DOMAIN/g" .env.prod
    
    # localhost인 경우 HTTP/WS로 변경, 그 외는 HTTPS/WSS 유지
    if [ "$DOMAIN" == "localhost" ]; then
        sed -i 's/https:\/\/localhost/http:\/\/localhost/g' .env.prod
        sed -i 's/wss:\/\/localhost/ws:\/\/localhost/g' .env.prod
        echo "✅ localhost HTTP/WS로 설정 완료!"
    else
        echo "✅ $DOMAIN HTTPS/WSS로 설정 완료!"
    fi
fi

# 보안 키 확인
if grep -q "your-secure-postgres-password-change-me" .env.prod; then
    echo "❌ .env.prod에서 데이터베이스 비밀번호를 변경하세요!"
    exit 1
fi

# Docker Compose로 프로덕션 환경 시작
echo "📦 프로덕션 컨테이너 빌드 및 시작 중..."
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d --build

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
    echo "   로그 확인: docker-compose --env-file .env.prod -f docker-compose.prod.yml logs -f"
    echo "   서비스 중지: docker-compose --env-file .env.prod -f docker-compose.prod.yml down"
    echo "   컨테이너 상태: docker-compose --env-file .env.prod -f docker-compose.prod.yml ps"
else
    echo "❌ 서비스 시작에 실패했습니다. 로그를 확인하세요:"
    echo "   docker-compose --env-file .env.prod -f docker-compose.prod.yml logs"
fi