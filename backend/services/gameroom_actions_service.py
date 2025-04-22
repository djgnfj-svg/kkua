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
from schemas.gameroom_schema import (
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
        
        # 게임 상태 확인
        if room.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임이 이미 시작되었거나 종료된 방입니다."
            )
        
        # 이미 참가 중인지 확인
        if self.repository.is_participant(room_id, guest.guest_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 해당 게임룸에 참가 중입니다."
            )
        
        # 다른 방에 이미 참여 중인지 확인
        should_redirect, active_room_id = self.guest_repository.check_active_game(guest.guest_id)
        if should_redirect and active_room_id != room_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이미 다른 게임방({active_room_id})에 참여 중입니다."
            )
        
        # 인원 수 확인
        current_participants = self.repository.count_participants(room_id)
        if current_participants >= room.max_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="방이 가득 찼습니다."
            )
        
        # 게임룸에 참가
        participant = self.repository.add_participant(room_id, guest.guest_id)
        
        # 참가자 수 업데이트
        self.repository.update_participant_count(room_id)
        
        # 비동기 함수를 스레드로 처리
        def run_async_broadcast():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast_room_update(
                room_id, 
                "user_joined", 
                {
                    "guest_id": guest.guest_id,
                    "nickname": guest.nickname
                }
            ))
            loop.close()
        
        # 참가자 목록 브로드캐스트
        threading.Thread(target=run_async_broadcast).start()
        
        return JoinGameroomResponse(
            room_id=room.room_id,
            title=room.title,
            guest_id=guest.guest_id,
            nickname=guest.nickname,
            participant_count=current_participants + 1
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
        
        # 참가자 확인
        if not self.repository.is_participant(room_id, guest.guest_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 게임룸에 참가하지 않았습니다."
            )
        
        # 방장인 경우
        is_creator = room.created_by == guest.guest_id
        
        # 게임룸에서 나가기
        self.repository.remove_participant(room_id, guest.guest_id)
        
        # 참가자 수 업데이트
        remaining_participants = self.repository.update_participant_count(room_id)
        
        # 방장이 나가고 다른 참가자가 있으면 방장 권한 이전
        if is_creator and remaining_participants > 0:
            next_participant = self.repository.get_oldest_participant(room_id)
            if next_participant:
                self.repository.transfer_ownership(room_id, next_participant.guest_id)
                
                # 비동기 함수를 스레드로 처리
                def run_async_broadcast_owner_change():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(ws_manager.broadcast_room_update(
                        room_id, 
                        "owner_changed", 
                        {
                            "new_owner_id": next_participant.guest_id,
                            "new_owner_nickname": next_participant.guest.nickname
                        }
                    ))
                    loop.close()
                
                # 방장 변경 알림
                threading.Thread(target=run_async_broadcast_owner_change).start()
                
        # 남은 참가자가 없으면 방 삭제
        elif remaining_participants == 0:
            self.repository.delete(room)
        
        # 비동기 함수를 스레드로 처리
        def run_async_broadcast_leave():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast_room_update(
                room_id, 
                "user_left", 
                {
                    "guest_id": guest.guest_id,
                    "nickname": guest.nickname
                }
            ))
            loop.close()
        
        # 참가자 퇴장 알림
        threading.Thread(target=run_async_broadcast_leave).start()
        
        return {"message": "성공적으로 게임룸에서 나갔습니다."}
    
    def start_game(self, room_id: int, request: Request) -> Dict[str, Any]:
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
                detail="이미 게임이 시작되었거나 종료된 상태입니다."
            )
        
        # 참가자 상태 확인 (모든 참가자가 READY 상태인지)
        participants = self.repository.find_room_participants(room_id)
        not_ready_participants = [p for p in participants if p.status != ParticipantStatus.READY]
        
        if not_ready_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="모든 참가자가 준비 상태가 아닙니다."
            )
        
        # 게임 시작 처리
        self.repository.start_game(room_id)
        
        # 게임 시작 시간
        start_time = datetime.now().isoformat()
        
        # 비동기 함수를 스레드로 처리
        def run_async_broadcast():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast_room_update(
                room_id, 
                "game_started", 
                {
                    "start_time": start_time,
                    "time_limit": room.time_limit
                }
            ))
            loop.close()
        
        # 게임 시작 알림
        threading.Thread(target=run_async_broadcast).start()
        
        return {
            "message": "게임이 시작되었습니다.",
            "start_time": start_time,
            "time_limit": room.time_limit
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