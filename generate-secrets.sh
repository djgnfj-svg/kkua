#!/bin/bash
# 배포를 위한 보안 키 생성 스크립트

echo "🔐 KKUA 배포용 보안 키 생성 중..."

# 32바이트 랜덤 키 생성
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)
DB_PASSWORD=$(openssl rand -base64 16)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 생성된 보안 키들:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔑 SECRET_KEY:"
echo "$SECRET_KEY"
echo ""
echo "🔑 JWT_SECRET:"
echo "$JWT_SECRET" 
echo ""
echo "🔑 DB_PASSWORD:"
echo "$DB_PASSWORD"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 이 키들을 복사해서 다음 파일들에 붙여넣으세요:"
echo ""
echo "1. backend/.env.prod"
echo "2. .env (Lightsail 서버의 환경변수 파일)"
echo ""
echo "⚠️  보안을 위해 이 키들을 안전한 곳에 저장하세요!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# .env 파일 생성
cat > .env.lightsail << EOF
# Lightsail 배포용 환경변수
DB_PASSWORD=$DB_PASSWORD
SECRET_KEY=$SECRET_KEY
JWT_SECRET=$JWT_SECRET
EOF

echo ""
echo "✅ .env.lightsail 파일이 생성되었습니다!"
echo "🚀 이제 Lightsail에 배포할 준비가 완료되었습니다."