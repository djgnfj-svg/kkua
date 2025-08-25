# 끄아(KKUA) V2 Makefile

.PHONY: help dev prod build up down logs restart clean backup deploy

# 기본값
COMPOSE_FILE_DEV = docker-compose.yml
COMPOSE_FILE_PROD = docker-compose.prod.yml

help: ## 도움말 표시
	@echo "끄아(KKUA) V2 - 사용 가능한 명령어:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# 개발 환경
dev: ## 개발 환경 시작
	docker compose -f $(COMPOSE_FILE_DEV) up -d
	@echo "개발 환경이 시작되었습니다:"
	@echo "- 프론트엔드: http://localhost:5173"
	@echo "- 백엔드 API: http://localhost:8000"
	@echo "- API 문서: http://localhost:8000/docs"

dev-build: ## 개발 환경 빌드 후 시작
	docker compose -f $(COMPOSE_FILE_DEV) up -d --build

dev-logs: ## 개발 환경 로그 확인
	docker compose -f $(COMPOSE_FILE_DEV) logs -f

dev-down: ## 개발 환경 중지
	docker compose -f $(COMPOSE_FILE_DEV) down

# 프로덕션 환경
prod: ## 프로덕션 환경 시작
	docker compose -f $(COMPOSE_FILE_PROD) up -d
	@echo "프로덕션 환경이 시작되었습니다:"
	@echo "- 게임: http://localhost"
	@echo "- API 문서: http://localhost/docs"

prod-build: ## 프로덕션 환경 빌드 후 시작
	docker compose -f $(COMPOSE_FILE_PROD) up -d --build

prod-logs: ## 프로덕션 환경 로그 확인
	docker compose -f $(COMPOSE_FILE_PROD) logs -f

prod-down: ## 프로덕션 환경 중지
	docker compose -f $(COMPOSE_FILE_PROD) down

# 공통 명령어
build: ## 이미지 빌드 (개발환경)
	docker compose -f $(COMPOSE_FILE_DEV) build

build-prod: ## 이미지 빌드 (프로덕션)
	docker compose -f $(COMPOSE_FILE_PROD) build

logs: ## 로그 확인 (개발환경)
	docker compose -f $(COMPOSE_FILE_DEV) logs -f

restart: ## 서비스 재시작 (개발환경)
	docker compose -f $(COMPOSE_FILE_DEV) restart

restart-prod: ## 서비스 재시작 (프로덕션)
	docker compose -f $(COMPOSE_FILE_PROD) restart

# 데이터베이스
db-connect: ## 데이터베이스 접속
	docker exec -it kkua-db-1 psql -U postgres -d kkua_db

db-connect-prod: ## 데이터베이스 접속 (프로덕션)
	docker exec -it kkua-db psql -U postgres -d kkua_db

# 백업
backup: ## 데이터베이스 백업
	./scripts/backup.sh

# 테스트
test-frontend: ## 프론트엔드 테스트
	docker compose -f $(COMPOSE_FILE_DEV) exec frontend npm test

test-backend: ## 백엔드 테스트
	docker compose -f $(COMPOSE_FILE_DEV) exec backend python -m pytest tests/ -v

lint-frontend: ## 프론트엔드 린트
	docker compose -f $(COMPOSE_FILE_DEV) exec frontend npm run lint

typecheck-frontend: ## 프론트엔드 타입체크
	docker compose -f $(COMPOSE_FILE_DEV) exec frontend npx tsc -b

# 정리
clean: ## 정리 (컨테이너, 이미지, 볼륨)
	docker compose -f $(COMPOSE_FILE_DEV) down -v --remove-orphans
	docker compose -f $(COMPOSE_FILE_PROD) down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

clean-prod: ## 프로덕션 정리
	docker compose -f $(COMPOSE_FILE_PROD) down -v --remove-orphans

# 모니터링
status: ## 서비스 상태 확인
	@echo "=== 개발 환경 ==="
	docker compose -f $(COMPOSE_FILE_DEV) ps
	@echo ""
	@echo "=== 프로덕션 환경 ==="
	docker compose -f $(COMPOSE_FILE_PROD) ps

health: ## 헬스체크
	@echo "=== 헬스체크 ==="
	@curl -f http://localhost/health 2>/dev/null && echo "✅ 웹 서비스: 정상" || echo "❌ 웹 서비스: 오류"
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✅ API 서비스: 정상" || echo "❌ API 서비스: 오류"

stats: ## 리소스 사용량
	docker stats --no-stream

# 배포
deploy: ## EC2 배포 (GitHub URL 필요)
	@if [ -z "$(GITHUB_URL)" ]; then \
		echo "사용법: make deploy GITHUB_URL=https://github.com/djgnfj-svg/kkua.git"; \
		exit 1; \
	fi
	./deploy.sh $(GITHUB_URL)

quick-deploy: ## 빠른 재배포
	./scripts/quick-deploy.sh

# 로그 관리
logs-backend: ## 백엔드 로그만 확인
	docker compose logs -f backend

logs-frontend: ## 프론트엔드 로그만 확인
	docker compose logs -f frontend

logs-nginx: ## Nginx 로그 확인 (프로덕션)
	docker compose -f $(COMPOSE_FILE_PROD) logs -f nginx