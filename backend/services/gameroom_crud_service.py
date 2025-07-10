"""
Gameroom CRUD Service - 게임룸 기본 CRUD 작업 전담
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from models.gameroom_model import Gameroom, GameStatus
from models.guest_model import Guest
from repositories.gameroom_repository import GameroomRepository
from schemas.gameroom_schema import GameroomResponse, CreateGameroomRequest


class GameroomCrudService:
    """게임룸 CRUD 작업 전담 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = GameroomRepository(db)
    
    def create_gameroom(
        self, 
        data: CreateGameroomRequest, 
        creator: Guest
    ) -> GameroomResponse:
        """새 게임룸을 생성합니다."""
        try:
            # 사용자당 방 개수 제한 확인 (선택적)
            user_rooms_count = self.db.query(Gameroom).filter(
                Gameroom.created_by == creator.guest_id,
                Gameroom.status == GameStatus.WAITING
            ).count()
            
            if user_rooms_count >= 3:  # 사용자당 최대 3개 방
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="동시에 생성할 수 있는 방의 개수를 초과했습니다."
                )
            
            # 방 생성 데이터 준비
            room_data = {
                "title": data.title,
                "max_players": data.max_players,
                "game_mode": data.game_mode,
                "time_limit": data.time_limit,
                "room_type": data.room_type,
                "created_by": creator.guest_id,
            }
            
            # 방 생성
            room = self.repository.create(room_data)
            
            # 방장을 참가자로 자동 추가
            self._add_creator_as_participant(room.room_id, creator.guest_id)
            
            self.db.commit()
            
            return self._map_to_response(room)
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"방 생성 실패: {str(e)}"
            )
    
    def _add_creator_as_participant(self, room_id: int, creator_id: int):
        """방장을 참가자로 추가"""
        from sqlalchemy import text
        
        self.db.execute(
            text("""
                INSERT INTO gameroom_participants 
                (room_id, guest_id, status, is_creator, joined_at, updated_at)
                VALUES (:room_id, :guest_id, 'waiting', true, :now, :now)
            """),
            {
                "room_id": room_id,
                "guest_id": creator_id,
                "now": datetime.now()
            }
        )
        
        # 참가자 수 업데이트
        self.db.execute(
            text("""
                UPDATE gamerooms 
                SET participant_count = 1, updated_at = :now
                WHERE room_id = :room_id
            """),
            {"room_id": room_id, "now": datetime.now()}
        )
    
    def get_gameroom(self, room_id: int) -> Optional[GameroomResponse]:
        """게임룸 정보를 조회합니다."""
        room = self.repository.find_by_id(room_id)
        if not room:
            return None
        
        return self._map_to_response(room)
    
    def get_all_gamerooms(
        self, 
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[GameroomResponse]:
        """게임룸 목록을 조회합니다."""
        from sqlalchemy import text
        
        # 기본 쿼리
        query = """
            SELECT r.*, COUNT(p.participant_id) as actual_participant_count
            FROM gamerooms r
            LEFT JOIN gameroom_participants p ON r.room_id = p.room_id AND p.left_at IS NULL
        """
        
        # 조건 추가
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if status_filter:
            conditions.append("r.status = :status")
            params["status"] = status_filter
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY r.room_id
            ORDER BY r.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        results = self.db.execute(text(query), params).fetchall()
        
        rooms = []
        for row in results:
            room = Gameroom(
                room_id=row.room_id,
                title=row.title,
                max_players=row.max_players,
                participant_count=row.actual_participant_count,
                game_mode=row.game_mode,
                time_limit=row.time_limit,
                status=row.status,
                room_type=row.room_type,
                created_by=row.created_by,
                created_at=row.created_at,
                updated_at=row.updated_at,
                started_at=row.started_at
            )
            rooms.append(self._map_to_response(room))
        
        return rooms
    
    def update_gameroom(
        self, 
        room_id: int, 
        data: Dict[str, Any], 
        requester: Guest
    ) -> Optional[GameroomResponse]:
        """게임룸을 업데이트합니다. (방장만 가능)"""
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방입니다."
            )
        
        # 방장 권한 확인
        if room.created_by != requester.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방장만 방 정보를 수정할 수 있습니다."
            )
        
        # 게임 중에는 수정 불가
        if room.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대기 중인 방만 수정할 수 있습니다."
            )
        
        try:
            updated_room = self.repository.update(room_id, data)
            if updated_room:
                self.db.commit()
                return self._map_to_response(updated_room)
            return None
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"방 정보 수정 실패: {str(e)}"
            )
    
    def delete_gameroom(self, room_id: int, requester: Guest) -> bool:
        """게임룸을 삭제합니다. (방장만 가능)"""
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 방입니다."
            )
        
        # 방장 권한 확인
        if room.created_by != requester.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방장만 방을 삭제할 수 있습니다."
            )
        
        try:
            success = self.repository.delete(room_id)
            if success:
                self.db.commit()
            return success
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"방 삭제 실패: {str(e)}"
            )
    
    def _map_to_response(self, room: Gameroom) -> GameroomResponse:
        """Gameroom 모델을 응답 스키마로 변환"""
        return GameroomResponse(
            room_id=room.room_id,
            title=room.title,
            max_players=room.max_players,
            participant_count=room.participant_count,
            game_mode=room.game_mode,
            time_limit=room.time_limit,
            status=room.status,
            room_type=room.room_type,
            created_by=room.created_by,
            created_at=room.created_at,
            updated_at=room.updated_at,
            started_at=room.started_at
        )