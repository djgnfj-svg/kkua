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
from middleware.rate_limiter import check_websocket_rate_limit

router = APIRouter(
    prefix="/ws/gamerooms",
    tags=["websockets"],
)


async def validate_websocket_connection(
    websocket: WebSocket, room_id: int, db: Session
) -> Tuple[Optional[Guest], bool]:
    """웹소켓 연결을 위한 세션 기반 인증 검증"""
    
    cookies = {}
    cookie_header = None
    
    cookie_header = websocket.headers.get('cookie')
    
    if cookie_header:
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                key, val = cookie.strip().split('=', 1)
                cookies[key] = val
    
    session_token = cookies.get('session_token')
    
    if not session_token:
        await websocket.close(code=4000, reason="세션 토큰이 필요합니다")
        return None, False
    
    session_token = session_token.strip('"')
    
    from utils.security import SecurityUtils
    session_data = SecurityUtils.verify_secure_token(session_token)
    
    if not session_data:
        session_store = get_session_store()
        session_data = session_store.get_session(session_token)
    
    if not session_data:
        await websocket.close(code=4001, reason="유효하지 않거나 만료된 세션입니다")
        return None, False
    
    guest_repo = GuestRepository(db)
    guest = guest_repo.find_by_id(session_data['guest_id'])
    
    if not guest:
        await websocket.close(code=4002, reason="게스트 정보를 찾을 수 없습니다")
        return None, False

    gameroom_repo = GameroomRepository(db)
    room = gameroom_repo.find_by_id(room_id)
    if not room:
        await websocket.close(code=4003, reason="게임룸이 존재하지 않습니다")
        return None, False

    participant = gameroom_repo.find_participant(room_id, guest.guest_id)
    is_participant = participant is not None
    is_creator = room.created_by == guest.guest_id

    if not (is_participant or is_creator):
        await websocket.close(code=4004, reason="게임룸에 참가하지 않은 게스트입니다")
        return None, False

    if is_creator and not is_participant:
        gameroom_repo.add_participant(room_id, guest.guest_id, is_creator=True)

    return guest, True


@router.websocket("/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_id: int, db: Session = Depends(get_db)
):
    """게임룸 웹소켓 연결 엔드포인트"""
    guest = None

    try:
        await websocket.accept()
        
        guest, is_valid = await validate_websocket_connection(websocket, room_id, db)
        if not is_valid:
            return

        message_service = WebSocketMessageService(db, ws_manager)
        
        await ws_manager.connect(websocket, room_id, guest.guest_id)

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

        await ws_manager.broadcast_to_room(
            room_id,
            {
                "type": "participants_update",
                "participants": participant_data,
                "message": f"{guest.nickname}님이 입장했습니다.",
            },
        )

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

        while True:
            data = await websocket.receive_text()
            
            # Rate Limiting 확인
            if not check_websocket_rate_limit(guest.guest_id):
                await ws_manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "메시지 전송 제한을 초과했습니다. 잠시 후 다시 시도해주세요.",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    websocket
                )
                continue
            
            try:
                message_data = json.loads(data)
                
                # 새로운 검증 시스템 시도 후 실패하면 기존 방식으로 fallback
                success = False
                if hasattr(message_service, 'validate_and_process_message'):
                    try:
                        success = await message_service.validate_and_process_message(
                            message_data, room_id, guest, websocket
                        )
                    except Exception as validation_error:
                        logger.warning(f"새로운 검증 시스템 실패, fallback 사용: {validation_error}")
                        success = False
                
                # 새로운 검증이 실패했거나 없으면 기존 처리 방식 사용
                if not success:
                    message_type = message_data.get("type")
                    
                    if message_type == "chat":
                        await message_service.handle_chat_message(message_data, room_id, guest)
                    elif message_type == "toggle_ready":
                        await message_service.handle_ready_toggle(websocket, room_id, guest)
                    elif message_type == "status_update":
                        await message_service.handle_status_update(message_data, websocket, room_id, guest)
                    elif message_type == "word_chain":
                        await message_service.handle_word_chain_message(message_data, websocket, room_id, guest)
            
            except json.JSONDecodeError:
                await ws_manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "잘못된 JSON 형식입니다.",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    websocket
                )
            except Exception as e:
                logger.error(f"메시지 처리 중 오류 발생: {e}", exc_info=True)
                await ws_manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "메시지 처리 중 오류가 발생했습니다.",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    websocket
                )

    except WebSocketDisconnect:
        if guest:
            logger.info(f"웹소켓 연결 해제: room_id={room_id}, guest_id={guest.guest_id}")
            await ws_manager.disconnect(websocket, room_id, guest.guest_id)
            
            # WebSocket 연결 해제 시 자동으로 방 나가기 처리 (DB 동기화)
            try:
                gameroom_service = GameroomService(db)
                # 방 나가기 처리 (DB에서 참가자 제거) - sync 메서드 호출
                result = gameroom_service.leave_gameroom(room_id, guest)
                logger.info(f"자동 방 나가기 처리 완료: room_id={room_id}, guest_id={guest.guest_id}, result={result}")
            except Exception as leave_error:
                logger.error(f"자동 방 나가기 처리 실패: {leave_error}", exc_info=True)
            
            await ws_manager.broadcast_room_update(
                room_id,
                "user_left",
                {"guest_id": guest.guest_id, "nickname": guest.nickname},
            )

    except Exception as e:
        logger.error(f"웹소켓 오류: {str(e)}", exc_info=True)
        if guest:
            await ws_manager.disconnect(websocket, room_id, guest.guest_id)
        try:
            await websocket.close(code=4003, reason=f"오류 발생: {str(e)}")
        except Exception:
            pass
    finally:
        # 연결 정리 시에도 DB 동기화 확인
        if guest and room_id:
            try:
                gameroom_service = GameroomService(db)
                # 혹시 놓친 케이스를 위한 최종 정리
                participants = gameroom_service.repository.find_room_participants(room_id)
                active_connections = ws_manager.get_room_connections(room_id)
                
                # WebSocket에는 없지만 DB에 남아있는 참가자들 정리
                for participant in participants:
                    guest_in_ws = any(conn.get('guest_id') == participant.guest_id 
                                    for conn in active_connections)
                    if not guest_in_ws:
                        # WebSocket에 없으면 DB에서도 제거 - sync 메서드 호출
                        gameroom_service.leave_gameroom(room_id, participant.guest)
                        logger.info(f"고아 참가자 정리: room_id={room_id}, guest_id={participant.guest_id}")
            except Exception as cleanup_error:
                logger.error(f"최종 정리 중 오류: {cleanup_error}", exc_info=True)


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