#!/bin/bash

# KKUA 프로덕션 배포 스크립트 (quick-deploy.sh와 동일)

cd "$(dirname "$0")/.."  # 프로젝트 루트로 이동

# quick-deploy.sh 실행
exec ./scripts/quick-deploy.sh