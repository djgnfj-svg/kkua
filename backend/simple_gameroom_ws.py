from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from datetime import datetime
from typing import Dict, List, Set

from db.postgres import get_db
from models.guest_model import Guest
from repositories.guest_repository import GuestRepository
from services.session_service import get_session_store
from utils.security import SecurityUtils

# 간단한 WebSocket 연결 관리
active_connections: Dict[int, Dict[str, WebSocket]] = {}  # {room_id: {guest_id: websocket}}

router = APIRouter(prefix="/ws/simple", tags=["simple-websockets"])
logger = logging.getLogger(__name__)


async def get_guest_from_websocket(websocket: WebSocket, db: Session) -> Guest:
    """WebSocket에서 게스트 인증 (단순화된 버전)"""
    try:
        cookies = {}
        cookie_header = websocket.headers.get("cookie")
        
        logger.info(f"🍪 Cookie 헤더: {cookie_header}")
        
        if cookie_header:
            for cookie in cookie_header.split(";"):
                if "=" in cookie:
                    key, val = cookie.strip().split("=", 1)
                    cookies[key] = val
        
        session_token = cookies.get("session_token")
        logger.info(f"🔑 세션 토큰: {session_token}")
        
        if not session_token:
            logger.warning("❌ 세션 토큰 없음")
            await websocket.close(code=4000, reason="세션 토큰이 필요합니다")
            return None
            
        session_token = session_token.strip('"')
        session_data = SecurityUtils.verify_secure_token(session_token)
        
        if not session_data:
            session_store = get_session_store()
            session_data = session_store.get_session(session_token)
        
        logger.info(f"📊 세션 데이터: {session_data}")
        
        if not session_data:
            logger.warning("❌ 유효하지 않은 세션")
            await websocket.close(code=4001, reason="유효하지 않은 세션입니다")
            return None
        
        guest_repo = GuestRepository(db)
        guest = guest_repo.find_by_id(session_data["guest_id"])
        
        logger.info(f"👤 게스트 찾음: {guest.nickname if guest else None}")
        
        if not guest:
            logger.warning("❌ 게스트를 찾을 수 없음")
            await websocket.close(code=4002, reason="게스트를 찾을 수 없습니다")
            return None
            
        return guest
        
    except Exception as e:
        logger.error(f"❌ 인증 중 오류: {e}")
        await websocket.close(code=4003, reason="인증 처리 중 오류가 발생했습니다")
        return None


def get_room_participants(db: Session, room_id: int) -> List[Dict]:
    """방 참가자 목록 조회 (직접 쿼리)"""
    query = text("""
        SELECT gp.guest_id, g.nickname, gp.is_creator, gp.status
        FROM gameroom_participants gp
        JOIN guests g ON gp.guest_id = g.guest_id
        WHERE gp.room_id = :room_id AND gp.left_at IS NULL
        ORDER BY gp.joined_at ASC
    """)
    
    result = db.execute(query, {"room_id": room_id}).fetchall()
    
    participants = []
    for row in result:
        participants.append({
            "guest_id": row[0],
            "nickname": row[1],
            "is_creator": bool(row[2]),
            "status": row[3],
        })
    
    return participants


def add_participant(db: Session, room_id: int, guest_id: int) -> bool:
    """참가자 추가 (직접 쿼리)"""
    try:
        # 이미 참가 중인지 확인
        check_query = text("""
            SELECT COUNT(*) FROM gameroom_participants 
            WHERE room_id = :room_id AND guest_id = :guest_id AND left_at IS NULL
        """)
        existing = db.execute(check_query, {"room_id": room_id, "guest_id": guest_id}).scalar()
        
        if existing > 0:
            return True  # 이미 참가 중
        
        # 참가자 추가
        insert_query = text("""
            INSERT INTO gameroom_participants (room_id, guest_id, joined_at, status, is_creator)
            VALUES (:room_id, :guest_id, :joined_at, 'WAITING', false)
        """)
        db.execute(insert_query, {
            "room_id": room_id,
            "guest_id": guest_id,
            "joined_at": datetime.now()
        })
        db.commit()
        return True
    except Exception as e:
        logger.error(f"참가자 추가 실패: {e}")
        db.rollback()
        return False


def remove_participant(db: Session, room_id: int, guest_id: int) -> bool:
    """참가자 제거 (직접 쿼리)"""
    try:
        update_query = text("""
            UPDATE gameroom_participants 
            SET left_at = :left_at, status = 'LEFT'
            WHERE room_id = :room_id AND guest_id = :guest_id AND left_at IS NULL
        """)
        db.execute(update_query, {
            "room_id": room_id,
            "guest_id": guest_id,
            "left_at": datetime.now()
        })
        db.commit()
        return True
    except Exception as e:
        logger.error(f"참가자 제거 실패: {e}")
        db.rollback()
        return False


async def broadcast_to_room(room_id: int, message: Dict):
    """방 전체에 메시지 브로드캐스트 (단순화)"""
    if room_id not in active_connections:
        return
    
    message_str = json.dumps(message)
    dead_connections = []
    
    for guest_id, websocket in active_connections[room_id].items():
        try:
            await websocket.send_text(message_str)
        except Exception as e:
            logger.warning(f"브로드캐스트 실패: guest_id={guest_id}, error={e}")
            dead_connections.append(guest_id)
    
    # 죽은 연결 정리
    for guest_id in dead_connections:
        if guest_id in active_connections[room_id]:
            del active_connections[room_id][guest_id]
    
    if not active_connections[room_id]:
        del active_connections[room_id]


@router.websocket("/gamerooms/{room_id}")
async def simple_websocket_endpoint(websocket: WebSocket, room_id: int, db: Session = Depends(get_db)):
    """간소화된 WebSocket 엔드포인트"""
    
    await websocket.accept()
    guest = None
    
    try:
        logger.info(f"🔌 WebSocket 연결 시도: room_id={room_id}")
        
        # 게스트 인증
        guest = await get_guest_from_websocket(websocket, db)
        if not guest:
            logger.warning("❌ 게스트 인증 실패")
            return
        
        logger.info(f"✅ WebSocket 연결: room_id={room_id}, guest_id={guest.guest_id}, nickname={guest.nickname}")
        
        # 연결 저장
        if room_id not in active_connections:
            active_connections[room_id] = {}
        active_connections[room_id][str(guest.guest_id)] = websocket
        
        # DB에 참가자 추가
        add_participant(db, room_id, guest.guest_id)
        
        # 현재 참가자 목록 조회
        participants = get_room_participants(db, room_id)
        
        # 입장 알림 브로드캐스트
        await broadcast_to_room(room_id, {
            "type": "participant_joined",
            "participants": participants,
            "message": f"{guest.nickname}님이 입장했습니다.",
            "timestamp": datetime.now().isoformat()
        })
        
        # 개인 연결 확인 메시지
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "연결되었습니다",
            "room_id": room_id,
            "guest_id": guest.guest_id
        }))
        
        # 메시지 루프
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "chat":
                    # 채팅 메시지 처리
                    content = message.get("message", "").strip()
                    if content:
                        await broadcast_to_room(room_id, {
                            "type": "chat",
                            "guest_id": guest.guest_id,
                            "user": {"nickname": guest.nickname},
                            "content": content,
                            "timestamp": datetime.now().isoformat()
                        })
                
                elif message_type == "toggle_ready":
                    # 준비 상태 토글 (간단히 구현)
                    await broadcast_to_room(room_id, {
                        "type": "ready_toggled",
                        "guest_id": guest.guest_id,
                        "nickname": guest.nickname,
                        "timestamp": datetime.now().isoformat()
                    })
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "잘못된 메시지 형식입니다."
                }))
            except Exception as e:
                logger.error(f"메시지 처리 오류: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": "메시지 처리 중 오류가 발생했습니다."
                }))
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket 연결 해제: room_id={room_id}, guest_id={guest.guest_id if guest else 'Unknown'}")
        
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        
    finally:
        # 연결 정리
        if guest and room_id in active_connections:
            guest_key = str(guest.guest_id)
            if guest_key in active_connections[room_id]:
                del active_connections[room_id][guest_key]
                
                # DB에서 참가자 제거
                remove_participant(db, room_id, guest.guest_id)
                
                # 퇴장 알림 브로드캐스트
                if active_connections[room_id]:  # 아직 다른 사람이 있다면
                    participants = get_room_participants(db, room_id)
                    await broadcast_to_room(room_id, {
                        "type": "participant_left",
                        "participants": participants,
                        "message": f"{guest.nickname}님이 퇴장했습니다.",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 방에 아무도 없으면 방 삭제
            if not active_connections[room_id]:
                del active_connections[room_id]
                logger.info(f"🗑️  빈 방 삭제: room_id={room_id}")