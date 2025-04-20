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
    GameroomResponse, GameroomListResponse, JoinGameroomResponse, 
    CreateGameroomRequest, GameroomDetailResponse
)
from ws_manager.connection_manager import ConnectionManager
from repositories.guest_repository import GuestRepository

# 웹소켓 연결 관리자
ws_manager = ConnectionManager()

class GameroomService:
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
    
    def list_gamerooms(self) -> List[Gameroom]:
        """활성화된 모든 게임룸을 조회합니다."""
        return self.repository.find_all_active()
    
    def create_gameroom(self, data: CreateGameroomRequest, guest_uuid: str) -> GameroomResponse:
        """게임룸 생성 메서드"""
        print(f"게임룸 생성 시작 - 데이터: {data}, UUID: {guest_uuid}")
        
        try:
            # 문자열 UUID를 UUID 객체로 변환
            uuid_obj = uuid.UUID(guest_uuid)
            guest = self.guest_repository.find_by_uuid(uuid_obj)
            
            if not guest:
                print(f"게스트를 찾을 수 없음: {guest_uuid}")
                raise HTTPException(status_code=404, detail="게스트를 찾을 수 없습니다")
            
            # 기존 게임방에 이미 참여 중인지 확인
            should_redirect, active_room_id = self.guest_repository.check_active_game(guest.guest_id)
            if should_redirect:
                print(f"기존 게임방 참여 중: {active_room_id}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"이미 다른 게임방({active_room_id})에 참여 중입니다"
                )
            
            # 데이터 준비
            room_data = {
                "title": data.title,
                "max_players": data.max_players,
                "game_mode": data.game_mode,
                "time_limit": data.time_limit,
                "created_by": guest.guest_id,
                "participant_count": 1  # 생성자 포함
            }
            
            # 게임룸 생성
            new_room = self.repository.create(room_data, guest.guest_id)
            print(f"게임룸 생성 성공: room_id={new_room.room_id}")
            
            return GameroomResponse(
                room_id=new_room.room_id,
                title=new_room.title,
                max_players=new_room.max_players,
                game_mode=new_room.game_mode,
                created_by=new_room.created_by,
                created_username=new_room.created_username,
                status=new_room.status.value,
                participant_count=new_room.participant_count,
                time_limit=new_room.time_limit
            )
        except Exception as e:
            print(f"게임룸 생성 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=f"게임룸 생성 실패: {str(e)}")
    
    def update_gameroom(self, room_id: int, request: Request, title: str = None, 
                        max_players: int = None, game_mode: str = None, time_limit: int = None):
        """게임룸 정보 업데이트"""
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
                detail="방장만 게임룸 정보를 수정할 수 있습니다."
            )
        
        # 게임룸 업데이트
        updated_room = self.repository.update(
            room_id, title, max_players, game_mode, time_limit
        )
        
        # 방 정보
        room_info = {
            "room_id": updated_room.room_id,
            "title": updated_room.title,
            "max_players": updated_room.max_players,
            "game_mode": updated_room.game_mode,
            "time_limit": updated_room.time_limit
        }
        
        # 비동기 호출을 스레드로 처리
        # 동기 컨텍스트에서 비동기 함수를 안전하게 호출
        def run_async_broadcast():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast_room_update(room_id, "room_updated", room_info))
            loop.close()
        
        # 백그라운드에서 실행
        threading.Thread(target=run_async_broadcast).start()
        
        return updated_room
    
    def delete_gameroom(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임룸을 삭제 처리합니다."""
        guest = self.get_guest_by_cookie(request)
        
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
            
        # 방 생성자만 삭제 가능
        if room.created_by != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방 생성자만 방을 삭제할 수 있습니다"
            )
        
        self.repository.delete(room)
        
        # 웹소켓으로 방 삭제 알림
        asyncio.create_task(ws_manager.broadcast_room_update(
            room_id, 
            "room_closed"
        ))
        
        return {"detail": "게임룸이 성공적으로 종료되었습니다"}
    
    def join_gameroom(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임룸 참가"""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다."
            )
        
        # 현재 참가자 수 확인
        current_participants = self.repository.count_participants(room_id)
        
        # None 체크 추가
        if current_participants is None:
            current_participants = 0
            print(f"참가자 수가 None이어서 0으로 설정함 - room_id: {room_id}")
        
        print(f"현재 참가자 수: {current_participants}, 최대 플레이어 수: {room.max_players}")
        
        # 참가자 수 체크
        if current_participants >= room.max_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임룸이 가득 찼습니다."
            )
        
        # 이미 참가 중인지 확인
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 게임룸에 참가 중입니다."
            )
        
        # 게임이 시작된 경우 참가 불가
        if room.status == GameStatus.PLAYING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임이 이미 시작되어 참가할 수 없습니다."
            )
        
        # 참가자 추가
        participant = self.repository.add_participant(room_id, guest.guest_id)
        
        # 방 정보
        guest_info = {
            "guest_id": guest.guest_id,
            "nickname": guest.nickname
        }
        
        # 비동기 호출을 스레드로 처리
        def run_async_broadcast():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast_room_update(
                room_id, 
                "user_joined", 
                guest_info
            ))
            loop.close()
        
        # 백그라운드에서 실행
        threading.Thread(target=run_async_broadcast).start()
        
        return {"message": "게임룸에 참가했습니다.", "room_id": room_id}
    
    def leave_gameroom(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임룸에서 나갑니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 참가 확인
        participation = self.repository.find_participant(room_id, guest.guest_id)
        
        if not participation:
            # 방 생성자인지 확인
            if room.created_by == guest.guest_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="방장은 방을 나갈 수 없습니다. 방을 삭제해주세요."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이 방에 참여하고 있지 않습니다."
                )
        
        # 참가자 제거
        self.repository.remove_participant(participation)
        
        # 웹소켓으로 참가자 퇴장 알림
        asyncio.create_task(ws_manager.broadcast_room_update(
            room_id, 
            "participant_left", 
            {
                "guest_id": guest.guest_id,
                "nickname": guest.nickname
            }
        ))
        
        return {"detail": f"게임룸({room_id})에서 성공적으로 나갔습니다."}
    
    def start_game(self, room_id: int, request: Request):
        """게임 시작"""
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
        
        # 게임 상태 업데이트
        updated_room = self.repository.update_status(room_id, GameStatus.PLAYING)
        
        # 비동기 호출을 스레드로 처리
        def run_async_broadcast():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ws_manager.broadcast_room_update(room_id, "game_started", {}))
            loop.close()
        
        # 백그라운드에서 실행
        threading.Thread(target=run_async_broadcast).start()
        
        return {"message": "게임이 시작되었습니다.", "room_id": room_id}
    
    def end_game(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임을 종료합니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 방 생성자만 게임 종료 가능
        if room.created_by != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방 생성자만 게임을 종료할 수 있습니다"
            )
        
        # 게임 상태 확인
        if room.status != GameStatus.PLAYING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="진행 중인 게임만 종료할 수 있습니다"
            )
        
        # 게임 종료 처리
        self.repository.update_game_status(room, GameStatus.FINISHED)
        
        # 웹소켓으로 게임 종료 알림
        asyncio.create_task(ws_manager.broadcast_room_update(
            room_id, 
            "game_ended"
        ))
        
        return {"detail": f"게임룸({room_id})의 게임이 종료되었습니다."}
    
    def get_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """특정 게임룸의 모든 참가자 정보를 반환합니다."""
        # 게임룸 존재 확인
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 현재 참여 중인 참가자들 조회
        participants = self.repository.find_room_participants(room_id)
        
        # 결과 구성
        result = []
        for p in participants:
            guest_info = {
                "guest_id": p.guest.guest_id,
                "nickname": p.guest.nickname,
                "uuid": str(p.guest.uuid),
                "is_room_creator": (p.guest.guest_id == room.created_by)
            }
            
            participant_info = {
                "participant_id": p.id,
                "status": p.status.value,
                "joined_at": p.joined_at
            }
            
            result.append({
                "guest": guest_info,
                "participant": participant_info
            })
        
        return result
    
    def check_active_game(self, request: Request, guest_uuid_str: str = None) -> Dict[str, Any]:
        """유저가 현재 게임 중인지 확인합니다."""
        # 쿼리 파라미터에서 게스트 UUID 가져오기
        if not guest_uuid_str:
            guest_uuid_str = request.cookies.get("kkua_guest_uuid")
            if not guest_uuid_str:
                return {"redirect": False}
        
        # 문자열을 UUID 객체로 변환
        try:
            guest_uuid = uuid.UUID(guest_uuid_str)
        except ValueError:
            return {"redirect": False}
        
        # 유저가 게임 중인지 확인
        should_redirect, room_id = self.guest_repository.check_active_game(guest_uuid)
        
        if should_redirect:
            return {
                "redirect": True,
                "room_id": room_id
            }
        
        return {"redirect": False}
    
    def update_participant_status(self, room_id: int, guest_id: int, status: str) -> Dict[str, str]:
        """참가자 상태를 업데이트합니다. (웹소켓을 통해 호출)"""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 참가자 조회
        participant = self.repository.find_participant(room_id, guest_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 참가자를 찾을 수 없습니다"
            )
        
        # 진행 중인 게임에서는 상태 변경 불가
        if room.status == GameStatus.PLAYING and status.upper() != "PLAYING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 진행 중에는 상태를 변경할 수 없습니다"
            )
        
        # 상태 업데이트
        updated_participant = self.repository.update_participant_status(participant.id, status.upper())
        
        # 웹소켓으로 상태 변경 알림
        asyncio.create_task(ws_manager.broadcast_room_update(
            room_id, 
            "status_changed",
            {
                "guest_id": guest_id,
                "status": updated_participant.status.value
            }
        ))
        
        return {"detail": "참가자 상태가 업데이트되었습니다."} 