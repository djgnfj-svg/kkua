from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy import text

from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus
from models.guest_model import Guest

class GameroomRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Gameroom]:
        rooms = self.db.query(Gameroom).filter(Gameroom.status == GameStatus.WAITING).all()
        return rooms
    
    def find_all_active(self) -> List[Gameroom]:
        """활성화된 모든 게임룸을 가져옵니다."""
        return self.get_all()  # 기존 get_all 메서드를 재사용
    
    def find_by_id(self, room_id: int) -> Optional[Gameroom]:
        """ID로 게임룸을 찾습니다."""
        room = self.db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
        return room
    
    def find_active_by_creator(self, guest_id: int) -> Optional[Gameroom]:
        """특정 게스트가 생성하고 아직 종료되지 않은 게임룸을 조회합니다."""
        return self.db.query(Gameroom).filter(
            Gameroom.created_by == guest_id,
            Gameroom.status != GameStatus.FINISHED
        ).first()
    
    def create(self, data: Dict[str, Any], guest_id: int) -> Gameroom:
        """게임룸을 생성합니다."""
        try:
            print(f"게임룸 생성 데이터: {data}, 생성자 ID: {guest_id}")
            
            # created_by가 없거나 None인 경우 guest_id를 사용
            if 'created_by' not in data or data['created_by'] is None:
                data['created_by'] = guest_id
                
            print(f"최종 created_by 값: {data['created_by']}")
                
            # 현재 시간 설정
            now = datetime.now()
            
            # 새 게임룸 생성
            new_room = Gameroom(
                title=data["title"],
                max_players=data["max_players"],
                game_mode=data["game_mode"],
                time_limit=data["time_limit"],
                status=GameStatus.WAITING,
                created_by=data["created_by"],
                created_at=now,
                updated_at=now,
                participant_count=1,
                room_type="normal"
            )
            
            self.db.add(new_room)
            self.db.flush()  # room_id를 얻기 위해 flush
            
            # 참가자 테이블에도 추가 (방장은 READY 상태로 설정)
            participant = GameroomParticipant(
                room_id=new_room.room_id,
                guest_id=data["created_by"],
                joined_at=now,
                status=ParticipantStatus.READY  # 방장은 READY 상태로 시작
            )
            
            self.db.add(participant)
            self.db.commit()
            
            print(f"게임룸 생성 완료: room_id={new_room.room_id}, created_by={new_room.created_by}")
            return new_room
        except Exception as e:
            self.db.rollback()
            print(f"게임룸 생성 중 오류 발생: {str(e)}")
            raise
    
    def update(self, room_id: int, title: str = None, max_players: int = None, 
               game_mode: str = None, time_limit: int = None):
        """게임룸 정보 업데이트"""
        room = self.find_by_id(room_id)
        if not room:
            return None
        
        # 값이 제공된 경우에만 업데이트
        if title is not None:
            room.title = title
        if max_players is not None:
            room.max_players = max_players
        if game_mode is not None:
            room.game_mode = game_mode
        if time_limit is not None:
            room.time_limit = time_limit
        
        # 변경 사항 저장
        self.db.commit()
        self.db.refresh(room)
        return room
    
    def delete(self, room: Gameroom) -> None:
        """게임룸을 삭제 처리합니다 (상태를 FINISHED로 변경)."""
        room.status = GameStatus.FINISHED
        self.db.commit()
    
    def find_participant(self, room_id: int, guest_id: int) -> Optional[GameroomParticipant]:
        """특정 게임룸에 참여 중인 참가자를 조회합니다."""
        return self.db.query(GameroomParticipant).filter(
            GameroomParticipant.guest_id == guest_id,
            GameroomParticipant.room_id == room_id,
            GameroomParticipant.left_at.is_(None)  # 아직 나가지 않은 상태
        ).first()
    
    def find_other_participation(self, guest_id: int, excluding_room_id: int) -> Optional[GameroomParticipant]:
        """특정 게스트가 다른 게임룸에 참여 중인지 확인합니다."""
        return self.db.query(GameroomParticipant).filter(
            GameroomParticipant.guest_id == guest_id,
            GameroomParticipant.room_id != excluding_room_id,
            GameroomParticipant.left_at.is_(None)
        ).first()
    
    def add_participant(self, room_id: int, guest_id: int) -> GameroomParticipant:
        """게임룸에 참가자를 추가합니다."""
        try:
            # 이미 참가중인지 확인
            existing = self.db.query(GameroomParticipant).filter(
                GameroomParticipant.room_id == room_id,
                GameroomParticipant.guest_id == guest_id,
                GameroomParticipant.left_at.is_(None)
            ).first()
            
            if existing:
                return existing
            
            # 새 참가자 추가
            participant = GameroomParticipant(
                room_id=room_id,
                guest_id=guest_id,
                joined_at=datetime.now(),
                status=ParticipantStatus.WAITING  # 일반 참가자는 WAITING 상태로 시작
            )
            
            self.db.add(participant)
            
            # 참가자 수 증가
            room = self.db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
            if room:
                room.participant_count = self.count_participants(room_id) + 1
            
            self.db.commit()
            return participant
        except Exception as e:
            self.db.rollback()
            print(f"참가자 추가 중 오류 발생: {str(e)}")
            raise
    
    def remove_participant(self, participation: GameroomParticipant) -> None:
        """참가자를 게임룸에서 제거합니다."""
        participation.left_at = datetime.now()
        participation.status = ParticipantStatus.LEFT
        
        # 인원수 감소
        room = self.find_by_id(participation.room_id)
        if room.participant_count > 0:
            room.participant_count -= 1
        
        self.db.commit()
    
    def update_game_status(self, room: Gameroom, status: GameStatus) -> Gameroom:
        """게임 상태를 업데이트합니다."""
        room.status = status
        
        # 참가자 상태 업데이트
        participant_status = None
        if status == GameStatus.PLAYING:
            participant_status = ParticipantStatus.PLAYING
        elif status == GameStatus.WAITING:
            participant_status = ParticipantStatus.WAITING
        
        if participant_status:
            participants = self.db.query(GameroomParticipant).filter(
                GameroomParticipant.room_id == room.room_id,
                GameroomParticipant.left_at.is_(None)
            ).all()
            
            for participant in participants:
                participant.status = participant_status
        
        self.db.commit()
        self.db.refresh(room)
        return room
    
    def find_room_participants(self, room_id: int) -> List[GameroomParticipant]:
        """특정 게임룸의 모든 참가자를 조회합니다."""
        return self.db.query(GameroomParticipant).filter(
            GameroomParticipant.room_id == room_id,
            GameroomParticipant.left_at.is_(None)
        ).all()
    
    def check_active_game(self, guest_uuid: uuid.UUID) -> Tuple[bool, Optional[int]]:
        """게스트가 현재 참여 중인 게임이 있는지 확인합니다."""
        guest = self.db.query(Guest).filter(Guest.uuid == guest_uuid).first()
        if not guest:
            return False, None
        
        return GameroomParticipant.should_redirect_to_game(self.db, guest.guest_id)
        
    def update_participant_status(self, participant_id: int, status_str: str) -> GameroomParticipant:
        """참가자 상태를 업데이트합니다."""
        participant = self.db.query(GameroomParticipant).filter(
            GameroomParticipant.id == participant_id
        ).first()
        
        if participant:
            new_status = ParticipantStatus[status_str.upper()]
            participant.status = new_status
            self.db.commit()
            self.db.refresh(participant)
        
        return participant
    
    def find_by_uuid(self, guest_uuid: uuid.UUID) -> Optional[Guest]:
        """UUID로 게스트를 조회합니다."""
        return self.db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    
    def count_participants(self, room_id: int) -> int:
        """방의 현재 참가자 수를 반환합니다."""
        try:
            count = self.db.query(GameroomParticipant).filter(
                GameroomParticipant.room_id == room_id
            ).count()
            print(f"방 ID {room_id}의 참가자 수: {count}")
            return count
        except Exception as e:
            print(f"참가자 수 조회 오류 - room_id: {room_id}, 오류: {str(e)}")
            # 오류 발생 시 0 반환 (None 대신)
            return 0
    
    def remove_participant(self, room_id: int, guest_id: int) -> None:
        """게임룸에서 참가자를 제거합니다."""
        try:
            participant = self.db.query(GameroomParticipant).filter(
                GameroomParticipant.room_id == room_id,
                GameroomParticipant.guest_id == guest_id
            ).first()
            
            if participant:
                self.db.delete(participant)
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"참가자 제거 오류: {str(e)}")
            raise

    def is_participant(self, room_id: int, guest_id: int) -> bool:
        """게스트가 게임룸의 참가자인지 확인합니다."""
        try:
            participant = self.db.query(GameroomParticipant).filter(
                GameroomParticipant.room_id == room_id,
                GameroomParticipant.guest_id == guest_id
            ).first()
            return participant is not None
        except Exception as e:
            print(f"참가자 확인 오류: {str(e)}")
            return False

    def get_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """게임룸의 모든 참가자를 가져옵니다."""
        try:
            # SQL 쿼리로 직접 조회 (JOIN 사용)
            query = text("""
                SELECT gp.guest_id, g.nickname, gp.is_creator, gp.joined_at
                FROM gameroom_participants gp
                JOIN guests g ON gp.guest_id = g.guest_id
                WHERE gp.room_id = :room_id
                ORDER BY gp.is_creator DESC, gp.joined_at ASC
            """)
            
            result = self.db.execute(query, {"room_id": room_id})
            
            participants = []
            for row in result:
                participants.append({
                    "guest_id": row[0],
                    "nickname": row[1],
                    "is_creator": row[2],
                    "joined_at": row[3]
                })
            
            return participants
        except Exception as e:
            print(f"참가자 목록 조회 오류: {str(e)}")
            return [] 