#!/usr/bin/env python3
"""
Docker 헬스체크 스크립트
애플리케이션 상태를 확인하고 건강성을 판단
"""
import sys
import asyncio
import aiohttp
import json
from pathlib import Path

# 부모 디렉토리를 Python path에 추가
sys.path.append(str(Path(__file__).parent.parent))

async def check_health():
    """헬스체크 실행"""
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 1. 기본 헬스체크 엔드포인트 확인
            async with session.get('http://localhost:8000/health') as response:
                if response.status != 200:
                    print(f"Health endpoint returned status: {response.status}")
                    return False
                
                health_data = await response.json()
                print(f"Health check response: {health_data}")
                
                # 2. 필수 서비스 상태 확인
                if not health_data.get('database', False):
                    print("Database connection failed")
                    return False
                
                if not health_data.get('redis', False):
                    print("Redis connection failed") 
                    return False
            
            # 3. WebSocket 엔드포인트 확인 (간단한 연결 테스트)
            try:
                import websockets
                uri = "ws://localhost:8000/ws/test"
                async with websockets.connect(uri, timeout=3) as websocket:
                    await websocket.send(json.dumps({"type": "ping"}))
                    response = await websocket.recv()
                    print("WebSocket connection test passed")
            except Exception as e:
                print(f"WebSocket test failed: {e}")
                # WebSocket 실패는 critical하지 않음 (선택적 체크)
        
        return True
        
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def main():
    """메인 함수"""
    try:
        result = asyncio.run(check_health())
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