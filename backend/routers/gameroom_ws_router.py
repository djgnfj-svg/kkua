from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime
import traceback

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from models.gameroom_model import ParticipantStatus
from services.gameroom_service import ws_manager  # 중요: 여기서 공유된 ws_manager 인스턴스 사용

router = APIRouter(
    prefix="/ws/gamerooms",
    tags=["websockets"],
)

@router.websocket("/{room_id}/{guest_uuid}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    guest_uuid: str,
    db: Session = Depends(get_db)
):
    """게임룸 웹소켓 연결 엔드포인트"""
    participant = None  # 참가자 변수 미리 선언
    guest = None        # 게스트 변수 미리 선언
    
    try:
        # 연결 수락 - 클라이언트와 핸드셰이크 완료
        await websocket.accept()
        print(f"웹소켓 초기 연결 수락: room_id={room_id}, guest_uuid={guest_uuid}")
        
        # UUID 형식 확인
        try:
            guest_uuid_obj = uuid.UUID(guest_uuid)
        except ValueError:
            print(f"UUID 형식 검증 실패: {guest_uuid}")
            await websocket.close(code=4000, reason="유효하지 않은 UUID 형식입니다")
            return
        
        # 게스트 조회
        guest_repo = GuestRepository(db)
        guest = guest_repo.find_by_uuid(guest_uuid_obj)
        
        if not guest:
            print(f"게스트 조회 실패: UUID={guest_uuid}")
            await websocket.close(code=4001, reason="유효하지 않은 게스트 UUID입니다")
            return
        
        # 게임룸 조회
        gameroom_repo = GameroomRepository(db)
        room = gameroom_repo.find_by_id(room_id)
        if not room:
            print(f"게임룸 조회 실패: room_id={room_id}")
            await websocket.close(code=4002, reason="게임룸이 존재하지 않습니다")
            return
        
        # 참가자 확인 - 방장이거나 참가자인 경우 허용
        participant = gameroom_repo.find_participant(room_id, guest.guest_id)
        is_participant = participant is not None
        is_creator = room.created_by == guest.guest_id
        
        if not (is_participant or is_creator):
            print(f"웹소켓 액세스 거부: guest_id={guest.guest_id}, room_id={room_id}")
            await websocket.close(code=4003, reason="게임룸에 참가하지 않은 게스트입니다")
            return
        
        # 방장이지만 참가자로 등록되지 않은 경우 참가자로 추가
        if is_creator and not is_participant:
            participant = gameroom_repo.add_participant(room_id, guest.guest_id)
            print(f"방장을 참가자로 추가: guest_id={guest.guest_id}, participant_id={participant.id}")
            
        try:
            # 웹소켓 연결 등록
            await ws_manager.connect(websocket, room_id, guest.guest_id)

            # 현재 방 참가자 정보 조회 (메소드명 수정: get_room_participants -> find_room_participants)
            participants = gameroom_repo.find_room_participants(room_id)
            participant_data = [
                {
                    "guest_id": p.guest.guest_id,
                    "nickname": p.guest.nickname,
                    "status": p.status.value,
                    "is_owner": room.created_by == p.guest.guest_id
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
                    
                    # 메시지 타입별 처리
                    if message_data.get("type") == "chat":
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
                    
                    elif message_data.get("type") == "toggle_ready":
                        # 준비 상태 토글 처리
                        if participant:
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
                                continue
                            
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
                        else:
                            await ws_manager.send_personal_message({
                                "type": "error",
                                "message": "준비 상태 변경 실패: 참가자 정보가 없습니다"
                            }, websocket)
                    
                    elif message_data.get("type") == "status_update":
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
                            continue
                        
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
            print(f"웹소켓 초기화 중 오류: {str(e)}")
            traceback.print_exc()
            
    except Exception as e:
        # 전역 예외 처리
        print(f"웹소켓 전역 오류: {str(e)}")
        traceback.print_exc()  # 상세 예외 정보 출력
        try:
            await websocket.close(code=4003, reason=f"오류 발생: {str(e)}")
        except:
            pass 