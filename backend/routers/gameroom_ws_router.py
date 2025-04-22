from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime
import traceback
from typing import Tuple, Optional, Dict, Any

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from models.gameroom_model import ParticipantStatus, GameroomParticipant
from models.guest_model import Guest
from services.gameroom_service import ws_manager  # 중요: 여기서 공유된 ws_manager 인스턴스 사용
from schemas.gameroom_ws_schema import WebSocketMessage, ChatMessage

router = APIRouter(
    prefix="/ws/gamerooms",
    tags=["websockets"],
)

# 도우미 함수: 게스트 및 참가자 검증
async def validate_connection(
    websocket: WebSocket, 
    room_id: int, 
    guest_uuid_str: str,
    db: Session
) -> Tuple[Optional[Guest], Optional[GameroomParticipant]]:
    """웹소켓 연결을 위한 게스트 및 참가자 유효성 검증"""
    # UUID 형식 확인
    try:
        guest_uuid_obj = uuid.UUID(guest_uuid_str)
    except ValueError:
        print(f"UUID 형식 검증 실패: {guest_uuid_str}")
        await websocket.close(code=4000, reason="유효하지 않은 UUID 형식입니다")
        return None, None
    
    # 게스트 조회
    guest_repo = GuestRepository(db)
    guest = guest_repo.find_by_uuid(guest_uuid_obj)
    
    if not guest:
        print(f"게스트 조회 실패: UUID={guest_uuid_str}")
        await websocket.close(code=4001, reason="유효하지 않은 게스트 UUID입니다")
        return None, None
    
    # 게임룸 조회
    gameroom_repo = GameroomRepository(db)
    room = gameroom_repo.find_by_id(room_id)
    if not room:
        print(f"게임룸 조회 실패: room_id={room_id}")
        await websocket.close(code=4002, reason="게임룸이 존재하지 않습니다")
        return None, None
    
    # 참가자 확인 - 방장이거나 참가자인 경우 허용
    participant = gameroom_repo.find_participant(room_id, guest.guest_id)
    is_participant = participant is not None
    is_creator = room.created_by == guest.guest_id
    
    if not (is_participant or is_creator):
        print(f"웹소켓 액세스 거부: guest_id={guest.guest_id}, room_id={room_id}")
        await websocket.close(code=4003, reason="게임룸에 참가하지 않은 게스트입니다")
        return None, None
    
    # 방장이지만 참가자로 등록되지 않은 경우 참가자로 추가
    if is_creator and not is_participant:
        participant = gameroom_repo.add_participant(room_id, guest.guest_id)
        print(f"방장을 참가자로 추가: guest_id={guest.guest_id}, participant_id={participant.id}")
    
    return guest, participant

# 도우미 함수: 메시지 처리
async def process_message(
    message_data: Dict[str, Any],
    websocket: WebSocket,
    room_id: int,
    guest: Guest,
    participant: GameroomParticipant,
    gameroom_repo: GameroomRepository
):
    """웹소켓 메시지 처리"""
    message_type = message_data.get("type")
    
    if message_type == "chat":
        # 채팅 메시지 처리
        nickname = guest.nickname if guest.nickname else f"게스트_{guest.uuid.hex[:8]}"
        await ws_manager.broadcast_to_room(
            room_id, 
            {
                "type": "chat",
                "guest_id": guest.guest_id,
                "nickname": nickname,
                "message": message_data.get("message", ""),
                "timestamp": message_data.get("timestamp", "")
            }
        )
    
    elif message_type == "toggle_ready":
        # 준비 상태 토글 처리
        if not participant:
            await ws_manager.send_personal_message({
                "type": "error",
                "message": "준비 상태 변경 실패: 참가자 정보가 없습니다"
            }, websocket)
            return
            
        current_status = participant.status
        
        # 현재 상태에 따라 토글
        if current_status == ParticipantStatus.WAITING:
            new_status = ParticipantStatus.READY
            is_ready = True
        elif current_status == ParticipantStatus.READY:
            new_status = ParticipantStatus.WAITING
            is_ready = False
        else:
            # 게임 중에는 상태 변경 불가
            await ws_manager.send_personal_message({
                "type": "error",
                "message": "게임 중에는 준비 상태를 변경할 수 없습니다"
            }, websocket)
            return
        
        # 참가자 상태 업데이트
        updated = gameroom_repo.update_participant_status(participant.id, new_status)
        
        # 준비 상태 변경 알림
        await ws_manager.broadcast_ready_status(
            room_id, 
            guest.guest_id, 
            is_ready,
            guest.nickname
        )
        
        # 개인 메시지로 상태 변경 확인
        await ws_manager.send_personal_message({
            "type": "ready_status_updated",
            "is_ready": is_ready
        }, websocket)
    
    elif message_type == "status_update":
        # 상태 업데이트 처리
        status = message_data.get("status", "WAITING")
        
        # 문자열을 열거형으로 변환
        try:
            status_enum = ParticipantStatus[status]
        except KeyError:
            await ws_manager.send_personal_message({
                "type": "error",
                "message": f"유효하지 않은 상태 값: {status}"
            }, websocket)
            return
        
        # 참가자 상태 업데이트
        if participant:  # 참가자가 존재하는지 확인
            updated = gameroom_repo.update_participant_status(participant.id, status_enum)
            
            # 상태 변경 알림
            await ws_manager.broadcast_room_update(
                room_id,
                "status_changed",
                {
                    "guest_id": guest.guest_id,
                    "nickname": guest.nickname,
                    "status": updated.status.value
                }
            )
        else:
            print(f"참가자 정보 없음: guest_id={guest.guest_id}")
            await ws_manager.send_personal_message({
                "type": "error",
                "message": "상태 업데이트 실패: 참가자 정보가 없습니다"
            }, websocket)

@router.websocket("/{room_id}/{guest_uuid}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    guest_uuid: str,
    db: Session = Depends(get_db)
):
    """게임룸 웹소켓 연결 엔드포인트"""
    guest = None
    
    try:
        # 연결 수락 - 클라이언트와 핸드셰이크 완료
        await websocket.accept()
        print(f"웹소켓 초기 연결 수락: room_id={room_id}, guest_uuid={guest_uuid}")
        
        # 사용자 및 권한 검증
        guest, participant = await validate_connection(websocket, room_id, guest_uuid, db)
        if not guest:
            return  # 검증 실패 시 조기 종료
            
        # 리포지토리 인스턴스 생성
        gameroom_repo = GameroomRepository(db)
        
        # 웹소켓 연결 등록
        await ws_manager.connect(websocket, room_id, guest.guest_id)

        # 현재 방 참가자 정보 조회
        participants = gameroom_repo.find_room_participants(room_id)
        participant_data = [
            {
                "guest_id": p.guest.guest_id,
                "nickname": p.guest.nickname,
                "status": p.status.value,
                "is_owner": p.guest.guest_id == p.gameroom.created_by
            }
            for p in participants
        ]
        
        # 새 참가자 입장 시 전체 참가자 목록 브로드캐스트
        await ws_manager.broadcast_to_room(room_id, {
            "type": "participants_update",
            "participants": participant_data,
            "message": f"{guest.nickname}님이 입장했습니다."
        })
        
        # 연결 성공 알림
        await ws_manager.send_personal_message({
            "type": "connected",
            "message": "게임룸 웹소켓에 연결되었습니다",
            "guest_id": guest.guest_id,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        print(f"웹소켓 연결 성공: room_id={room_id}, guest_id={guest.guest_id}")
        
        try:
            # 메시지 수신 루프
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                print(f"웹소켓 메시지 수신: {message_data}")
                
                # 메시지 처리 (도우미 함수 사용)
                await process_message(message_data, websocket, room_id, guest, participant, gameroom_repo)
                
        except WebSocketDisconnect:
            # 연결 종료 처리
            print(f"웹소켓 연결 종료됨: room_id={room_id}, guest_id={guest.guest_id}")
            await ws_manager.disconnect(websocket, room_id, guest.guest_id)
            
            # 다른 참가자들에게 퇴장 알림
            await ws_manager.broadcast_room_update(
                room_id, 
                "user_left", 
                {
                    "guest_id": guest.guest_id,
                    "nickname": guest.nickname
                }
            )
            
        except Exception as e:
            # 기타 예외 처리
            print(f"웹소켓 오류: {str(e)}")
            traceback.print_exc()  # 상세 예외 정보 출력
            if guest:
                await ws_manager.disconnect(websocket, room_id, guest.guest_id)
                
    except Exception as e:
        # 전역 예외 처리
        print(f"웹소켓 전역 오류: {str(e)}")
        traceback.print_exc()  # 상세 예외 정보 출력
        try:
            await websocket.close(code=4003, reason=f"오류 발생: {str(e)}")
        except:
            pass 

@router.get("/documentation", tags=["websockets"])
def websocket_documentation():
    """
    # 웹소켓 API 문서
    
    ## 연결 URL
    - `ws://서버주소/ws/gamerooms/{room_id}/{guest_uuid}`
    
    ## 메시지 형식
    모든 메시지는 JSON 형식이며 다음 구조를 따릅니다:
    ```json
    {
        "type": "메시지_타입",
        "data": { /* 메시지별 데이터 */ }
    }
    ```
    
    ## 지원하는 메시지 유형
    1. **chat**: 채팅 메시지
       - 송신: `{"type": "chat", "data": {"message": "내용"}}`
       - 수신: `{"type": "chat", "guest_id": 123, "nickname": "사용자", "message": "내용", "timestamp": "..."}`
    
    2. **toggle_ready**: 준비 상태 변경
       - 송신: `{"type": "toggle_ready"}`
       - 수신: `{"type": "ready_status_changed", "guest_id": 123, "is_ready": true}`
    
    3. **user_joined**: 사용자 입장 (서버에서만 전송)
       - 수신: `{"type": "user_joined", "data": {"guest_id": 123}}`
    
    4. **user_left**: 사용자 퇴장 (서버에서만 전송)
       - 수신: `{"type": "user_left", "data": {"guest_id": 123, "nickname": "사용자"}}`
    """
    return {
        "message": "위 문서를 참고하세요.",
        "websocket_url": "/ws/gamerooms/{room_id}/{guest_uuid}"
    } 