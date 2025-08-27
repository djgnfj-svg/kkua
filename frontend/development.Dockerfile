# 개발용 Dockerfile
FROM node:20-alpine

WORKDIR /app

# 패키지 파일 복사 및 의존성 설치
COPY package*.json ./
RUN npm ci

# 개발 서버 포트 노출
EXPOSE 5173

# 개발 서버 실행 (소스코드는 volume으로 마운트)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]