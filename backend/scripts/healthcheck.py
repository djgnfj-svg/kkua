#!/usr/bin/env python3
"""
Docker 헬스체크 스크립트 (간단한 버전)
애플리케이션 상태를 확인하고 건강성을 판단
"""
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path

def check_health():
    """헬스체크 실행"""
    try:
        # HTTP 헬스체크 엔드포인트 확인
        req = urllib.request.Request('http://localhost:8000/health')
        req.add_header('User-Agent', 'HealthCheck/1.0')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                print(f"Health endpoint returned status: {response.status}")
                return False
            
            health_data = json.loads(response.read().decode())
            print(f"Health check response: {health_data}")
            
            # 서비스 상태 확인
            if health_data.get('status') != 'healthy':
                print(f"Service status: {health_data.get('status')}")
                return False
        
        return True
        
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"URL error: {e.reason}")
        return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def main():
    """메인 함수"""
    try:
        result = check_health()
        if result:
            print("✓ Health check passed")
            sys.exit(0)
        else:
            print("✗ Health check failed")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Health check error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()