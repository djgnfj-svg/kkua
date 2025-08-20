#!/bin/bash
"""
KKUA 자동 배포 스크립트
개발/스테이징/프로덕션 환경별 배포 자동화
"""

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 설정 변수
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-development}"
VERSION="${2:-latest}"

# 환경별 설정
case $ENVIRONMENT in
    "development")
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.dev"
        ;;
    "staging")
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.staging"
        ;;
    "production")
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.prod"
        ;;
    *)
        log_error "지원되지 않는 환경입니다: $ENVIRONMENT"
        echo "사용법: $0 [development|staging|production] [version]"
        exit 1
        ;;
esac

# 함수 정의
check_prerequisites() {
    log_info "전제 조건 확인 중..."
    
    # Docker 설치 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # Docker Compose 설치 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    # 환경 파일 존재 확인
    if [[ ! -f "$PROJECT_ROOT/$ENV_FILE" ]]; then
        log_warning "환경 파일이 없습니다: $ENV_FILE"
        log_info "예제 파일을 복사하여 환경 설정을 완료하세요."
        
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/$ENV_FILE"
            log_success "예제 환경 파일이 복사되었습니다: $ENV_FILE"
            log_warning "배포 전에 환경 설정을 확인하고 수정하세요!"
        fi
    fi
    
    log_success "전제 조건 확인 완료"
}

run_tests() {
    log_info "테스트 실행 중..."
    
    cd "$PROJECT_ROOT"
    
    # 백엔드 테스트
    if [[ "$ENVIRONMENT" != "production" ]]; then
        log_info "백엔드 테스트 실행..."
        docker-compose -f docker-compose.yml run --rm backend-test || {
            log_error "백엔드 테스트 실패"
            return 1
        }
        
        # 프론트엔드 테스트 (있는 경우)
        if [[ -d "$PROJECT_ROOT/frontend" ]]; then
            log_info "프론트엔드 테스트 실행..."
            docker-compose -f docker-compose.yml --profile frontend run --rm frontend npm test || {
                log_error "프론트엔드 테스트 실패"
                return 1
            }
        fi
    else
        log_warning "프로덕션 환경에서는 테스트를 건너뜁니다."
    fi
    
    log_success "테스트 완료"
}

build_images() {
    log_info "Docker 이미지 빌드 중..."
    
    cd "$PROJECT_ROOT"
    
    # 기존 이미지 정리 (선택적)
    if [[ "$ENVIRONMENT" = "production" ]]; then
        log_info "사용하지 않는 Docker 이미지 정리..."
        docker system prune -f
    fi
    
    # 이미지 빌드
    export ENVIRONMENT
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache || {
        log_error "Docker 이미지 빌드 실패"
        exit 1
    }
    
    # 이미지 태깅 (프로덕션)
    if [[ "$ENVIRONMENT" = "production" ]]; then
        log_info "이미지 태깅 중..."
        docker tag kkua-backend:latest "kkua-backend:$VERSION"
        
        if [[ -d "$PROJECT_ROOT/frontend" ]]; then
            docker tag kkua-frontend:latest "kkua-frontend:$VERSION"
        fi
    fi
    
    log_success "Docker 이미지 빌드 완료"
}

backup_data() {
    if [[ "$ENVIRONMENT" = "production" ]]; then
        log_info "데이터베이스 백업 중..."
        
        BACKUP_DIR="$PROJECT_ROOT/backups"
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        
        mkdir -p "$BACKUP_DIR"
        
        # PostgreSQL 백업
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db \
            pg_dump -U postgres kkua_prod > "$BACKUP_DIR/$BACKUP_FILE" || {
            log_error "데이터베이스 백업 실패"
            exit 1
        }
        
        # 백업 파일 압축
        gzip "$BACKUP_DIR/$BACKUP_FILE"
        
        # 오래된 백업 파일 정리 (7일 이상)
        find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
        
        log_success "데이터베이스 백업 완료: $BACKUP_FILE.gz"
    fi
}

deploy_services() {
    log_info "서비스 배포 중..."
    
    cd "$PROJECT_ROOT"
    
    # 환경 변수 설정
    export ENVIRONMENT
    export VERSION
    
    # 기존 서비스 중지
    log_info "기존 서비스 중지 중..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down || true
    
    # 데이터베이스 마이그레이션 (필요한 경우)
    if [[ -f "$PROJECT_ROOT/backend/alembic.ini" ]]; then
        log_info "데이터베이스 마이그레이션 실행..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm backend-migrate || {
            log_error "데이터베이스 마이그레이션 실패"
            exit 1
        }
    fi
    
    # 서비스 시작
    log_info "새로운 서비스 시작 중..."
    if [[ "$ENVIRONMENT" = "production" ]]; then
        # 프로덕션: 모든 서비스 포함
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile monitoring up -d || {
            log_error "서비스 시작 실패"
            exit 1
        }
    else
        # 개발/스테이징: 기본 서비스만
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d || {
            log_error "서비스 시작 실패"
            exit 1
        }
    fi
    
    log_success "서비스 배포 완료"
}

health_check() {
    log_info "서비스 상태 확인 중..."
    
    cd "$PROJECT_ROOT"
    
    # 서비스 상태 대기
    log_info "서비스 시작 대기 중 (최대 60초)..."
    
    MAX_ATTEMPTS=12
    ATTEMPT=1
    
    while [[ $ATTEMPT -le $MAX_ATTEMPTS ]]; do
        log_info "헬스체크 시도 $ATTEMPT/$MAX_ATTEMPTS"
        
        # HTTP 헬스체크
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "백엔드 서비스 정상 작동 확인"
            break
        fi
        
        if [[ $ATTEMPT -eq $MAX_ATTEMPTS ]]; then
            log_error "헬스체크 실패 - 서비스가 정상적으로 시작되지 않았습니다."
            log_info "서비스 로그 확인:"
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs --tail=20 backend
            exit 1
        fi
        
        sleep 5
        ((ATTEMPT++))
    done
    
    # 컨테이너 상태 확인
    log_info "컨테이너 상태 확인:"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    log_success "서비스 상태 확인 완료"
}

performance_check() {
    if [[ "$ENVIRONMENT" = "production" ]]; then
        log_info "성능 확인 중..."
        
        # 간단한 로드 테스트
        log_info "기본 로드 테스트 실행..."
        
        # curl을 이용한 간단한 응답 시간 테스트
        RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/health)
        
        log_info "응답 시간: ${RESPONSE_TIME}초"
        
        # 응답 시간이 1초를 초과하면 경고
        if (( $(echo "$RESPONSE_TIME > 1.0" | bc -l) )); then
            log_warning "응답 시간이 느립니다: ${RESPONSE_TIME}초"
        else
            log_success "응답 시간 정상: ${RESPONSE_TIME}초"
        fi
    fi
}

cleanup() {
    log_info "정리 작업 수행 중..."
    
    # 사용하지 않는 Docker 리소스 정리
    docker system prune -f
    
    log_success "정리 작업 완료"
}

rollback() {
    log_error "배포 실패 - 롤백을 수행합니다..."
    
    cd "$PROJECT_ROOT"
    
    # 이전 버전으로 롤백 (백업이 있는 경우)
    if [[ "$ENVIRONMENT" = "production" ]] && [[ -n "$PREVIOUS_VERSION" ]]; then
        log_info "이전 버전으로 롤백 중: $PREVIOUS_VERSION"
        
        export VERSION="$PREVIOUS_VERSION"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        
        log_success "롤백 완료"
    else
        log_warning "롤백할 이전 버전이 없습니다."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    fi
}

show_status() {
    log_info "배포 완료 상태:"
    echo "================================"
    echo "환경: $ENVIRONMENT"
    echo "버전: $VERSION"
    echo "시간: $(date)"
    echo "================================"
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    echo ""
    log_info "접속 정보:"
    echo "- API: http://localhost:8000"
    echo "- Health Check: http://localhost:8000/health"
    echo "- API Docs: http://localhost:8000/docs"
    
    if [[ "$ENVIRONMENT" = "production" ]]; then
        echo "- Monitoring: http://localhost:3001 (Grafana)"
        echo "- Metrics: http://localhost:9090 (Prometheus)"
    fi
}

# 메인 실행 로직
main() {
    log_info "KKUA 배포 시작 - 환경: $ENVIRONMENT, 버전: $VERSION"
    
    # 에러 발생 시 롤백 설정
    trap 'rollback' ERR
    
    # 배포 프로세스 실행
    check_prerequisites
    
    if [[ "$ENVIRONMENT" != "production" ]]; then
        run_tests
    fi
    
    backup_data
    build_images
    deploy_services
    health_check
    performance_check
    cleanup
    
    # 성공 시 trap 해제
    trap - ERR
    
    log_success "배포 성공!"
    show_status
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi