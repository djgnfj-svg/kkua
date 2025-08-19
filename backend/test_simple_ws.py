from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

router = APIRouter(prefix="/ws/test", tags=["test-websockets"])
logger = logging.getLogger(__name__)

# 임시 연결 저장소
active_connections = {}


@router.websocket("/gamerooms/{room_id}")
async def test_websocket_endpoint(websocket: WebSocket, room_id: int):
    """테스트용 WebSocket (인증 없음)"""
    
    await websocket.accept()
    logger.info(f"🧪 테스트 WebSocket 연결: room_id={room_id}")
    
    try:
        # 연결 저장
        if room_id not in active_connections:
            active_connections[room_id] = []
        active_connections[room_id].append(websocket)
        
        # 연결 성공 메시지
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "테스트 연결 성공!",
            "room_id": room_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # 모든 연결에 새 유저 알림
        message = {
            "type": "participant_joined", 
            "message": f"새 사용자가 방 {room_id}에 참가했습니다!",
            "participants": [{"guest_id": 999, "nickname": "테스트유저", "is_creator": False}],
            "timestamp": datetime.now().isoformat()
        }
        
        for conn in active_connections[room_id]:
            try:
                await conn.send_text(json.dumps(message))
            except:
                pass
        
        # 메시지 루프
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                logger.info(f"📨 테스트 메시지 받음: {msg}")
                
                if msg.get("type") == "chat":
                    # 채팅 브로드캐스트
                    chat_message = {
                        "type": "chat",
                        "content": msg.get("message", ""),
                        "user": {"nickname": "테스트유저"},
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    for conn in active_connections[room_id]:
                        try:
                            await conn.send_text(json.dumps(chat_message))
                        except:
                            pass
                            
            except Exception as e:
                logger.error(f"❌ 메시지 처리 오류: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"🔌 테스트 WebSocket 연결 해제: room_id={room_id}")
        
    except Exception as e:
        logger.error(f"❌ 테스트 WebSocket 오류: {e}")
        
    finally:
        # 연결 정리
        if room_id in active_connections:
            try:
                active_connections[room_id].remove(websocket)
            except:
                pass
            if not active_connections[room_id]:
                del active_connections[room_id]