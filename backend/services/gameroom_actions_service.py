from fastapi import HTTPException, status, Request, WebSocket
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import json
from datetime import datetime
import threading

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, ParticipantStatus
from models.guest_model import Guest
from schemas.gameroom_actions_schema import (
    JoinGameroomResponse
)
from ws_manager.connection_manager import ConnectionManager
from repositories.guest_repository import GuestRepository

# 웹소켓 연결 관리자 (gameroom_service.py와 공유)
from services.gameroom_service import ws_manager

class GameroomActionsService:
    def __init__(self, repository: GameroomRepository, guest_repository: GuestRepository):
        self.repository = repository
        self.guest_repository = guest_repository
    
    def get_guest_by_cookie(self, request: Request) -> Guest:
        """쿠키에서 UUID를 추출하여 게스트를 반환합니다."""
        guest_uuid_str = request.cookies.get("kkua_guest_uuid")
        if not guest_uuid_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게스트 UUID가 필요합니다. 쿠키에 kkua_guest_uuid가 없습니다."
            )
        
        try:
            guest_uuid = uuid.UUID(guest_uuid_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 UUID 형식입니다."
            )
        
        guest = self.guest_repository.find_by_uuid(guest_uuid)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="유효하지 않은 게스트 UUID입니다."
            )
        
        return guest
    
    def join_gameroom(self, room_id: int, request: Request) -> JoinGameroomResponse:
        """게임룸에 참가합니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다."
            )
        
        # 게임 상태 확인 - Enum과 문자열 모두 처리
        room_status = room.status
        if isinstance(room_status, str):
            is_waiting = room_status == GameStatus.WAITING.value
        else:
            is_waiting = room_status == GameStatus.WAITING
        
        if not is_waiting:
            print(f"게임 상태 오류: room_id={room_id}, status={room_status}, type={type(room_status)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임이 이미 시작되었거나 종료된 방입니다."
            )
        
        # 이미 참가 중인지 확인 (left_at이 NULL인 참가자만 체크)
        participant = self.repository.check_participation(room_id, guest.guest_id)
        if participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 해당 게임룸에 참가 중입니다."
            )
        
        # 다른 방에 참여 중인지 확인 (left_at이 NULL인 다른 방 참가자만 체크)
        active_participants = self.repository.find_active_participants(guest.guest_id)
        
        # 다른 방에 참여 중인 경우 (현재 참가하려는 방 제외)
        other_active_rooms = [p for p in active_participants if p.room_id != room_id]
        if other_active_rooms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이미 다른 게임방({other_active_rooms[0].room_id})에 참여 중입니다."
            )
        
        # 인원 수 확인
        current_participants = self.repository.count_participants(room_id)
        if current_participants >= room.max_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="방이 가득 찼습니다."
            )
        
        # 게임룸에 참가 (새 참가자 생성)
        new_participant = self.repository.add_participant(room_id, guest.guest_id)
        
        # 참가자 수 업데이트
        self.repository.update_participant_count(room_id)
        
        # 웹소켓 이벤트 발송 (게임룸 참가 알림)
        if hasattr(self, 'ws_manager'):
            asyncio.create_task(self.ws_manager.broadcast_room_update(
                room_id, 
                "player_joined", 
                {
                    "guest_id": guest.guest_id,
                    "nickname": guest.nickname,
                    "joined_at": datetime.now().isoformat(),
                    "is_creator": False
                }
            ))
        
        return JoinGameroomResponse(
            room_id=room_id,
            guest_id=guest.guest_id,
            message="게임룸에 참가했습니다."
        )
    
    def leave_gameroom(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임룸에서 나갑니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다."
            )
        
        # 참가자 조회
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant or participant.left_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 게임룸에 참가 중이 아닙니다."
            )
        
        print(f"게임룸 나가기: 방ID={room_id}, 게스트ID={guest.guest_id}, 참가자ID={participant.participant_id}")
        
        # 게임 진행 중인지 확인
        if room.status == GameStatus.PLAYING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 진행 중에는 나갈 수 없습니다."
            )
        
        # 방장인지 확인
        is_creator = (room.created_by == guest.guest_id)
        print(f"방장 여부: {is_creator}")
        
        # 참가자 상태 업데이트
        # 직접 업데이트하여 확실하게 처리
        current_time = datetime.now()
        result = self.repository.update_participant_left(
            participant.participant_id, 
            current_time,
            ParticipantStatus.LEFT.value
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="참가자 상태 업데이트에 실패했습니다."
            )
        
        print(f"참가자 상태 업데이트 완료: left_at={current_time}, status=LEFT")
        
        # 방장이 나간 경우 방 삭제
        if is_creator:
            print(f"방장(게스트ID={guest.guest_id})이 나가서 게임룸(ID={room_id})을 삭제합니다.")
            
            # 방 상태 업데이트 (DELETED)
            room.status = GameStatus.DELETED.value if isinstance(GameStatus.DELETED.value, str) else GameStatus.DELETED
            room.updated_at = current_time
            self.repository.db.commit()
            print(f"게임룸 상태 업데이트 완료: status=DELETED")
            
            # 남은 참가자들을 강제 퇴장 처리
            self.repository.update_all_participants_left(room_id, current_time)
            print("남은 모든 참가자 퇴장 처리 완료")
            
            # 웹소켓 이벤트 발송 (방 삭제)
            if hasattr(self, 'ws_manager'):
                asyncio.create_task(self.ws_manager.broadcast_room_update(
                    room_id,
                    "room_deleted",
                    {
                        "room_id": room_id,
                        "message": "방장이 퇴장하여 게임룸이 삭제되었습니다."
                    }
                ))
            
            return {"message": "방장이 퇴장하여 게임룸이 삭제되었습니다."}
        else:
            # 일반 참가자가 나간 경우, 참가자 수만 업데이트
            self.repository.update_participant_count(room_id)
            print(f"참가자 수 업데이트 완료")
            
            # 웹소켓 이벤트 발송 (참가자 퇴장)
            if hasattr(self, 'ws_manager'):
                asyncio.create_task(self.ws_manager.broadcast_room_update(
                    room_id,
                    "player_left",
                    {
                        "guest_id": guest.guest_id,
                        "nickname": guest.nickname,
                        "left_at": current_time.isoformat()
                    }
                ))
            
            return {"message": "게임룸에서 퇴장했습니다."}
    
    def start_game(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임을 시작합니다. 방장만 게임을 시작할 수 있습니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다."
            )
        
        # 방장 확인
        if room.created_by != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방장만 게임을 시작할 수 있습니다."
            )
        
        # 게임 상태 확인
        if room.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대기 중인 게임방만 시작할 수 있습니다."
            )
        
        # 최소 2명 이상 확인
        participant_count = self.repository.count_participants(room_id)
        if participant_count < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임을 시작하려면 최소 2명의 참가자가 필요합니다."
            )
        
        # 모든 참가자 준비 상태 확인
        all_ready = self.repository.check_all_ready(room_id)
        if not all_ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="모든 참가자가 준비 상태여야 게임을 시작할 수 있습니다."
            )
        
        # 게임 시작
        result = self.repository.start_game(room_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="게임 시작에 실패했습니다."
            )
        
        print(f"게임 시작 완료: 방ID={room_id}")
        
        # 웹소켓 이벤트 발송 (게임 시작)
        if hasattr(self, 'ws_manager'):
            asyncio.create_task(self.ws_manager.broadcast_room_update(
                room_id,
                "game_started",
                {
                    "room_id": room_id,
                    "started_at": datetime.now().isoformat(),
                    "message": "게임이 시작되었습니다!"
                }
            ))
        
        return {
            "message": "게임이 시작되었습니다!",
            "status": "PLAYING"
        }
    
    def end_game(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임을 종료합니다. 방장만 게임을 종료할 수 있습니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다."
            )
        
        # 방장 확인
        if room.created_by != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방장만 게임을 종료할 수 있습니다."
            )
        
        # 게임 상태 확인
        if room.status != GameStatus.PLAYING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임이 시작되지 않았거나 이미 종료된 상태입니다."
            )
        
        # 게임 종료 처리
        self.repository.end_game(room_id)
        
        # 비동기 함수를 스레드로 처리
        def run_async_broadcast():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast_room_update(
                room_id, 
                "game_ended", 
                {
                    "end_time": datetime.now().isoformat()
                }
            ))
            loop.close()
        
        # 게임 종료 알림
        threading.Thread(target=run_async_broadcast).start()
        
        return {"message": "게임이 종료되었습니다."}
    
    def get_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """게임룸의 참가자 목록을 조회합니다."""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다."
            )
        
        # 참가자 목록 조회
        participants = self.repository.get_participants(room_id)
        return participants
    
    def check_active_game(self, request: Request, guest_uuid_str: str = None) -> Dict[str, Any]:
        """유저가 현재 참여 중인 게임이 있는지 확인합니다."""
        if guest_uuid_str:
            # URL 파라미터로 UUID가 제공된 경우
            try:
                guest_uuid = uuid.UUID(guest_uuid_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 UUID 형식입니다."
                )
        else:
            # 쿠키에서 UUID 가져오기
            guest_uuid_str = request.cookies.get("kkua_guest_uuid")
            if not guest_uuid_str:
                return {
                    "has_active_game": False,
                    "room_id": None
                }
                
            try:
                guest_uuid = uuid.UUID(guest_uuid_str)
            except ValueError:
                return {
                    "has_active_game": False,
                    "room_id": None
                }
        
        # UUID로 게스트 조회
        guest = self.guest_repository.find_by_uuid(guest_uuid)
        if not guest:
            return {
                "has_active_game": False,
                "room_id": None
            }
        
        # 활성화된 게임 확인
        should_redirect, active_room_id = self.guest_repository.check_active_game(guest.guest_id)
        
        return {
            "has_active_game": should_redirect,
            "room_id": active_room_id
        }
    
    def check_if_owner(self, room_id: int, request: Request) -> Dict[str, bool]:
        """현재 게스트가 특정 게임룸의 방장인지 확인합니다."""
        try:
            guest = self.get_guest_by_cookie(request)
            
            # 게임룸 조회
            room = self.repository.find_by_id(room_id)
            if not room:
                return {"is_owner": False}
            
            # 방장 여부 확인
            is_owner = room.created_by == guest.guest_id
            
            return {"is_owner": is_owner}
        except HTTPException:
            return {"is_owner": False}
    
    def toggle_ready_status(self, room_id: int, request: Request) -> Dict[str, Any]:
        """참가자의 준비 상태를 토글합니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다."
            )
        
        # 참가자 조회
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant or participant.left_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 게임룸에 참가 중이 아닙니다."
            )
        
        # 게임 상태 확인
        if room.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대기 중인 게임방에서만 준비 상태를 변경할 수 있습니다."
            )
        
        # 방장 확인 - 방장은 항상 준비 상태
        is_creator = (room.created_by == guest.guest_id)
        if is_creator:
            return {
                "status": ParticipantStatus.READY.value,
                "message": "방장은 항상 준비 상태입니다.",
                "is_ready": True
            }
        
        # 현재 상태 확인 및 새 상태 설정
        current_status = participant.status
        print(f"현재 참가자 상태: {current_status}")
        
        new_status = None
        if current_status == ParticipantStatus.WAITING.value or current_status == ParticipantStatus.WAITING:
            new_status = ParticipantStatus.READY.value
            is_ready = True
            message = "준비 완료!"
        else:
            new_status = ParticipantStatus.WAITING.value
            is_ready = False
            message = "준비 취소!"
        
        # 상태 업데이트
        result = self.repository.update_participant_status(participant.participant_id, new_status)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="참가자 상태 업데이트에 실패했습니다."
            )
        
        print(f"참가자 상태 업데이트 완료: {current_status} -> {new_status}")
        
        # 웹소켓 이벤트 발송 (참가자 상태 변경)
        if hasattr(self, 'ws_manager'):
            asyncio.create_task(self.ws_manager.broadcast_room_update(
                room_id,
                "player_ready_changed",
                {
                    "guest_id": guest.guest_id,
                    "nickname": guest.nickname,
                    "status": new_status,
                    "is_ready": is_ready
                }
            ))
        
        return {
            "status": new_status,
            "message": message,
            "is_ready": is_ready
        } 