# Node.js 베이스 이미지 선택 (필요한 Node 버전에 맞게 조정)
FROM node:22.9-alpine

# 작업 디렉토리 생성
WORKDIR /app
# npm 버전 공유
RUN npm install -g npm@11.2.0

# 나머지 소스 코드 복사
COPY . .

RUN npm install
# React 개발 서버 포트 노출
EXPOSE 3000

# 컨테이너 실행 시 React 앱 시작
CMD ["npm", "start"]
