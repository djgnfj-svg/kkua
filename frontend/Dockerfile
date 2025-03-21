# Node.js 베이스 이미지 선택 (필요한 Node 버전에 맞게 조정)
FROM node:23-alpine

# 작업 디렉토리 생성
WORKDIR /app

# package.json과 package-lock.json을 먼저 복사하여 의존성 설치 캐시 활용
COPY package.json package-lock.json ./
RUN npm install

# 나머지 소스 코드 복사
COPY . .

# React 개발 서버 포트 노출
EXPOSE 3000

# 컨테이너 실행 시 React 앱 시작
CMD ["npm", "start"]
