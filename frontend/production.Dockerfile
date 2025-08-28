# Multi-stage build for production
FROM node:20-alpine as builder

WORKDIR /app

# 패키지 파일 복사 및 의존성 설치
COPY package*.json ./
RUN npm ci --only=production

# 소스 코드 복사
COPY . .

# Build arguments 정의
ARG VITE_API_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000/ws  
ARG VITE_NODE_ENV=production
ARG VITE_DEBUG=false
ARG VITE_GAME_TIMER_DURATION=30000
ARG VITE_RECONNECT_INTERVAL=5000
ARG VITE_MAX_RECONNECT_ATTEMPTS=3

# 환경변수로 설정 (Vite가 빌드 시점에 사용)
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}
ENV VITE_NODE_ENV=${VITE_NODE_ENV}
ENV VITE_DEBUG=${VITE_DEBUG}
ENV VITE_GAME_TIMER_DURATION=${VITE_GAME_TIMER_DURATION}
ENV VITE_RECONNECT_INTERVAL=${VITE_RECONNECT_INTERVAL}
ENV VITE_MAX_RECONNECT_ATTEMPTS=${VITE_MAX_RECONNECT_ATTEMPTS}
ENV NODE_ENV=production

# 디버깅: 빌드 환경변수 확인
RUN echo "=== Build Environment Variables ===" && \
    echo "VITE_API_URL: ${VITE_API_URL}" && \
    echo "VITE_WS_URL: ${VITE_WS_URL}" && \
    echo "VITE_NODE_ENV: ${VITE_NODE_ENV}" && \
    echo "NODE_ENV: ${NODE_ENV}"

# 프로덕션 빌드 실행
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# 빌드된 파일을 nginx 디렉토리로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# nginx가 non-root 사용자로 실행되도록 설정
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# 포트 노출
EXPOSE 5173

# nginx 실행
CMD ["nginx", "-g", "daemon off;"]