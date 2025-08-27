# Multi-stage build for production
FROM node:20-alpine as builder

WORKDIR /app

# 패키지 파일 복사 및 의존성 설치
COPY package*.json ./
RUN npm ci

# 소스 코드 복사
COPY . .

# 프로덕션 빌드
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# 빌드된 파일을 nginx로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx 설정 (SPA를 위한 fallback 설정)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 포트 노출
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]