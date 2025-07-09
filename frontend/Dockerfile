# Node.js 베이스 이미지 (필요에 따라 버전 변경 가능)
FROM node:22.9

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사 (의존성 설치 효율을 위해)
COPY package.json package-lock.json ./

# 의존성 설치
RUN npm install

# 소스 코드 전체 복사
COPY . .

# React 개발 서버 포트 오픈
EXPOSE 3000

# 앱 실행
CMD ["npm", "start"]
