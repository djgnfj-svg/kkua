from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus
from models.gameroom_participant import ParticipantStatus
from models.guest_model import Guest
from schemas.gameroom import GameroomResponse

class GameroomService:
    def __init__(self, repository: GameroomRepository, db: Session):
        self.repository = repository
        self.db = db
    
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
        
        guest = self.db.query(Guest).filter(Guest.uuid == guest_uuid).first()
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="유효하지 않은 게스트 UUID입니다."
            )
        
        return guest
    
    def list_gamerooms(self) -> List[Gameroom]:
        """활성화된 모든 게임룸을 조회합니다."""
        return self.repository.find_all_active()
    
    def create_gameroom(self, request: Request, title: str = None, max_players: int = None, 
                       game_mode: str = None, time_limit: int = None) -> Gameroom:
        """새 게임룸을 생성합니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 이미 생성한 방이 있는지 확인
        existing_room = self.repository.find_active_by_creator(guest.guest_id)
        if existing_room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 생성한 방이 있습니다. 새로운 방을 만들기 전에 기존 방을 삭제해주세요."
            )
        
        # 기본값 설정
        room_data = {
            "title": title if title is not None else "새로운 방",
            "max_players": max_players if max_players is not None else 4,
            "game_mode": game_mode if game_mode is not None else "normal",
            "time_limit": time_limit if time_limit is not None else 60,
            "created_by": guest.guest_id,
            "status": GameStatus.WAITING
        }
        
        return self.repository.create(room_data, guest.guest_id)
    
    def update_gameroom(self, room_id: int, request: Request, title: str = None, 
                        max_players: int = None, game_mode: str = None, 
                        time_limit: int = None) -> Gameroom:
        """게임룸 정보를 업데이트합니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        db_room = self.repository.find_by_id(room_id)
        if not db_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 방 생성자만 수정 가능
        if db_room.created_by != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방 생성자만 수정할 수 있습니다"
            )
        
        # 게임중인 방은 수정 불가
        if db_room.status == GameStatus.PLAYING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 진행 중인 방은 수정할 수 없습니다"
            )
        
        # 업데이트할 값 설정
        update_data = {
            "title": title,
            "max_players": max_players,
            "game_mode": game_mode,
            "time_limit": time_limit
        }
        
        return self.repository.update(db_room, update_data)
    
    def delete_gameroom(self, room_id: int) -> Dict[str, str]:
        """게임룸을 삭제 처리합니다."""
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
        
        self.repository.delete(room)
        return {"detail": "게임룸이 성공적으로 종료되었습니다"}
    
    def join_gameroom(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임룸에 참가합니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 이미 방 생성자인지 확인
        if room.created_by == guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 해당 방의 생성자입니다."
            )
        
        # 최대 인원 초과 확인
        if room.participant_count >= room.max_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="방이 가득 찼습니다."
            )
        
        # 게임 진행중인지 확인
        if room.status == GameStatus.PLAYING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임이 이미 시작되었습니다."
            )
        
        # 게임이 종료되었는지 확인
        if room.status == GameStatus.FINISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="종료된 게임입니다."
            )
        
        # 이미 참여중인지 확인
        existing_participation = self.repository.find_participant(room_id, guest.guest_id)
        if existing_participation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 이 방에 참여중입니다."
            )
        
        # 다른 방에 이미 참여 중인지 확인
        other_participation = self.repository.find_other_participation(guest.guest_id, room_id)
        if other_participation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"다른 방(방 ID: {other_participation.room_id})에 이미 참여 중입니다. 먼저 해당 방에서 나가야 합니다."
            )
        
        # 참가자 추가
        self.repository.add_participant(room_id, guest.guest_id)
        
        return {"detail": f"게임룸({room_id})에 성공적으로 참여하였습니다."}
    
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
        
        # 참여 기록 확인
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
        
        return {"detail": f"게임룸({room_id})에서 성공적으로 나갔습니다."}
    
    def start_game(self, room_id: int, request: Request) -> Dict[str, str]:
        """게임을 시작합니다."""
        guest = self.get_guest_by_cookie(request)
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 방 생성자만 게임 시작 가능
        if room.created_by != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방 생성자만 게임을 시작할 수 있습니다"
            )
        
        # 게임 상태 확인
        if room.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대기 중인 방만 게임을 시작할 수 있습니다"
            )
        
        # 최소 인원 확인 (예: 최소 2명 이상)
        if room.participant_count < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임을 시작하려면 최소 2명 이상의 참가자가 필요합니다"
            )
        
        # 게임 시작 처리
        self.repository.update_game_status(room, GameStatus.PLAYING)
        
        return {"detail": f"게임룸({room_id})의 게임이 시작되었습니다."}
    
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
        should_redirect, room_id = self.repository.check_active_game(guest_uuid)
        
        if should_redirect:
            return {
                "redirect": True,
                "room_id": room_id
            }
        
        return {"redirect": False} 