from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
from datetime import datetime
import traceback
from typing import Tuple, Optional

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from models.guest_model import Guest
from services.gameroom_service import ws_manager
from services.session_service import get_session_store
from services.websocket_message_service import WebSocketMessageService

router = APIRouter(
    prefix="/ws/gamerooms",
    tags=["websockets"],
)


async def validate_websocket_connection(
    websocket: WebSocket, room_id: int, db: Session
) -> Tuple[Optional[Guest], bool]:
    """웹소켓 연결을 위한 세션 기반 인증 검증"""
    
    # 웹소켓 헤더에서 쿠키 추출
    cookies = {}
    cookie_header = None
    
    # 헤더에서 쿠키 찾기
    for name, value in websocket.headers:
        if name.lower() == b'cookie':
            cookie_header = value.decode('utf-8')
            break
    
    if cookie_header:
        # 쿠키 파싱
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                key, val = cookie.strip().split('=', 1)
                cookies[key] = val
    
    # 세션 토큰 추출
    session_token = cookies.get('session_token')
    if not session_token:
        await websocket.close(code=4000, reason="세션 토큰이 필요합니다")
        return None, False
    
    # 세션 유효성 검사
    session_store = get_session_store()
    session_data = session_store.get_session(session_token)
    if not session_data:
        await websocket.close(code=4001, reason="유효하지 않거나 만료된 세션입니다")
        return None, False
    
    # 게스트 조회
    guest_repo = GuestRepository(db)
    guest = guest_repo.find_by_id(session_data['guest_id'])
    
    if not guest:
        await websocket.close(code=4002, reason="게스트 정보를 찾을 수 없습니다")
        return None, False

    # 게임룸 및 참가자 권한 확인
    gameroom_repo = GameroomRepository(db)
    room = gameroom_repo.find_by_id(room_id)
    if not room:
        await websocket.close(code=4003, reason="게임룸이 존재하지 않습니다")
        return None, False

    # 참가자 확인 - 방장이거나 참가자인 경우 허용
    participant = gameroom_repo.find_participant(room_id, guest.guest_id)
    is_participant = participant is not None
    is_creator = room.created_by == guest.guest_id

    if not (is_participant or is_creator):
        await websocket.close(code=4004, reason="게임룸에 참가하지 않은 게스트입니다")
        return None, False

    # 방장이지만 참가자로 등록되지 않은 경우 참가자로 추가
    if is_creator and not is_participant:
        gameroom_repo.add_participant(room_id, guest.guest_id, is_creator=True)
        print(f"방장을 참가자로 추가: guest_id={guest.guest_id}")

    return guest, True


@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_id: int, db: Session = Depends(get_db)
):
    """게임룸 웹소켓 연결 엔드포인트"""
    guest = None

    try:
        # 연결 수락
        await websocket.accept()
        
        # 사용자 및 권한 검증
        guest, is_valid = await validate_websocket_connection(websocket, room_id, db)
        if not is_valid:
            return

        # 메시지 서비스 초기화
        message_service = WebSocketMessageService(db, ws_manager)
        
        # 웹소켓 연결 등록
        await ws_manager.connect(websocket, room_id, guest.guest_id)

        # 현재 방 참가자 정보 조회 및 브로드캐스트
        gameroom_repo = GameroomRepository(db)
        participants = gameroom_repo.find_room_participants(room_id)
        participant_data = [
            {
                "guest_id": p.guest.guest_id,
                "nickname": p.guest.nickname,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "is_owner": p.guest.guest_id == p.gameroom.created_by,
            }
            for p in participants
        ]

        # 새 참가자 입장 알림
        await ws_manager.broadcast_to_room(
            room_id,
            {
                "type": "participants_update",
                "participants": participant_data,
                "message": f"{guest.nickname}님이 입장했습니다.",
            },
        )

        # 연결 성공 알림
        await ws_manager.send_personal_message(
            {
                "type": "connected",
                "message": "게임룸 웹소켓에 연결되었습니다",
                "guest_id": guest.guest_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        # 메시지 수신 루프
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 메시지 타입별 처리
            message_type = message_data.get("type")
            
            if message_type == "chat":
                await message_service.handle_chat_message(message_data, room_id, guest)
            elif message_type == "toggle_ready":
                await message_service.handle_ready_toggle(websocket, room_id, guest)
            elif message_type == "status_update":
                await message_service.handle_status_update(message_data, websocket, room_id, guest)
            elif message_type == "word_chain":
                await message_service.handle_word_chain_message(message_data, websocket, room_id, guest)

    except WebSocketDisconnect:
        # 연결 종료 처리
        if guest:
            await ws_manager.disconnect(websocket, room_id, guest.guest_id)
            await ws_manager.broadcast_room_update(
                room_id,
                "user_left",
                {"guest_id": guest.guest_id, "nickname": guest.nickname},
            )

    except Exception as e:
        # 예외 처리
        print(f"웹소켓 오류: {str(e)}")
        traceback.print_exc()
        if guest:
            await ws_manager.disconnect(websocket, room_id, guest.guest_id)
        try:
            await websocket.close(code=4003, reason=f"오류 발생: {str(e)}")
        except Exception:
            pass


@router.get("/documentation", tags=["websockets"])
def websocket_documentation():
    """웹소켓 API 문서"""
    return {
        "message": "WebSocket API for game room communication",
        "websocket_url": "/ws/gamerooms/{room_id}",
        "authentication": "session_token cookie required",
        "supported_message_types": [
            "chat - 채팅 메시지",
            "toggle_ready - 준비 상태 토글",
            "status_update - 상태 업데이트",
            "word_chain - 끝말잇기 게임 액션"
        ]
    }