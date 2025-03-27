# 베이스 이미지 선택 (최신 Python 3.13-slim 사용)
FROM python:3.13-slim

# 작업 디렉토리 생성
WORKDIR /app

# 의존성 파일 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 소스 코드 전체 복사
COPY . .

# 컨테이너 실행 시 uvicorn을 모듈 방식으로 실행
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
