from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
import uuid

router = APIRouter(prefix="/ws/test", tags=["test-websockets"])
logger = logging.getLogger(__name__)

# 임시 연결 저장소 - {room_id: {user_id: {websocket, user_info}}}
active_connections = {}
# 사용자 정보 저장소
room_participants = {}


async def broadcast_to_room(room_id: int, message: dict, exclude_user: str = None):
    """방의 모든 사용자에게 메시지 브로드캐스트"""
    if room_id not in active_connections:
        return
        
    for user_id, user_data in active_connections[room_id].items():
        if exclude_user and user_id == exclude_user:
            continue
            
        try:
            await user_data["websocket"].send_text(json.dumps(message))
        except:
            # 연결이 끊어진 경우 무시
            pass

def get_room_participants(room_id: int):
    """방의 참가자 목록 반환"""
    if room_id not in room_participants:
        return []
    return list(room_participants[room_id].values())

@router.websocket("/gamerooms/{room_id}")
async def test_websocket_endpoint(websocket: WebSocket, room_id: int):
    """인터랙티브 테스트 WebSocket"""
    
    await websocket.accept()
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    
    # 고유 사용자 ID 생성
    user_id = str(uuid.uuid4())[:8]
    user_nickname = f"사용자{user_id[:4]}"
    
    logger.info(f"🧪 새 사용자 접속: room_id={room_id}, user_id={user_id}, nickname={user_nickname}")
    
    try:
        # 방 초기화
        if room_id not in active_connections:
            active_connections[room_id] = {}
            room_participants[room_id] = {}
        
        # 첫 번째 사용자는 방장으로 설정
        is_creator = len(room_participants[room_id]) == 0
        
        # 사용자 정보 저장
        user_info = {
            "guest_id": user_id,
            "nickname": user_nickname,
            "is_creator": is_creator,
            "status": "waiting",
            "is_ready": False
        }
        
        active_connections[room_id][user_id] = {
            "websocket": websocket,
            "user_info": user_info
        }
        room_participants[room_id][user_id] = user_info
        
        # 연결 성공 메시지
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": f"환영합니다! {user_nickname}님",
            "user": user_info,
            "room_id": room_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # 다른 사용자들에게 새 참가자 알림
        participants = get_room_participants(room_id)
        join_message = {
            "type": "participant_joined",
            "message": f"🎉 {user_nickname}님이 입장하셨습니다!",
            "participants": participants,
            "new_user": user_info,
            "timestamp": datetime.now().isoformat()
        }
        
        await broadcast_to_room(room_id, join_message)
        
        # 메시지 처리 루프
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                logger.info(f"📨 {user_nickname} 메시지: {msg}")
                
                if msg.get("type") == "chat":
                    # 채팅 메시지 브로드캐스트
                    chat_message = {
                        "type": "chat",
                        "content": msg.get("message", ""),
                        "user": user_info,
                        "guest_id": user_id,
                        "nickname": user_nickname,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await broadcast_to_room(room_id, chat_message)
                    
                elif msg.get("type") == "toggle_ready":
                    # 준비 상태 토글
                    user_info["is_ready"] = not user_info["is_ready"]
                    user_info["status"] = "ready" if user_info["is_ready"] else "waiting"
                    
                    room_participants[room_id][user_id] = user_info
                    
                    ready_message = {
                        "type": "ready_toggled",
                        "message": f"🎯 {user_nickname}님이 {'준비완료' if user_info['is_ready'] else '준비취소'} 하셨습니다!",
                        "user": user_info,
                        "participants": get_room_participants(room_id),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await broadcast_to_room(room_id, ready_message)
                    
            except Exception as e:
                logger.error(f"❌ 메시지 처리 오류: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"🔌 사용자 퇴장: {user_nickname} (room_id={room_id})")
        
    except Exception as e:
        logger.error(f"❌ WebSocket 오류: {e}, user={user_nickname}")
        
    finally:
        # 연결 정리
        if room_id in active_connections and user_id in active_connections[room_id]:
            del active_connections[room_id][user_id]
            
        if room_id in room_participants and user_id in room_participants[room_id]:
            del room_participants[room_id][user_id]
            
        # 다른 사용자들에게 퇴장 알림
        if room_id in room_participants:
            leave_message = {
                "type": "participant_left",
                "message": f"👋 {user_nickname}님이 퇴장하셨습니다.",
                "participants": get_room_participants(room_id),
                "left_user": user_info,
                "timestamp": datetime.now().isoformat()
            }
            
            await broadcast_to_room(room_id, leave_message)
            
        # 방이 비어있으면 정리
        if room_id in active_connections and not active_connections[room_id]:
            del active_connections[room_id]
        if room_id in room_participants and not room_participants[room_id]:
            del room_participants[room_id]