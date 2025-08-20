# Frontend Dockerfile for KKUA
FROM node:20-alpine

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 파일 복사 및 의존성 설치
COPY package*.json ./
RUN npm ci

# 소스 코드 복사
COPY . .

# 개발 서버 시작 (기본값)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# 포트 노출
EXPOSE 5173