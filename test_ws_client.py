#!/usr/bin/env python3
import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    uri = "ws://localhost:8000/ws/test/gamerooms/2"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ 연결 성공: {uri}")
            
            # 메시지 수신
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 받은 메시지: {data}")
            
            # 채팅 메시지 전송
            await websocket.send(json.dumps({
                "type": "chat",
                "message": "테스트 메시지입니다!"
            }))
            print("📤 채팅 메시지 전송")
            
            # 응답 수신
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 받은 메시지: {data}")
            
            # 추가 메시지 수신 (participant_joined)
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 받은 메시지: {data}")
            
            # 10초 대기
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())