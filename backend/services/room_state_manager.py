"""
Room state management service for handling concurrent room operations
"""

import threading
from typing import Dict, Set, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status

from models.gameroom_model import Gameroom, GameroomParticipant, GameStatus, ParticipantStatus
from models.guest_model import Guest
from repositories.gameroom_repository import GameroomRepository


class RoomStateManager:
    """방 상태 관리자 - 동시성 제어 및 상태 일관성 보장"""
    
    def __init__(self):
        # 방별 락 관리 (세밀한 락킹)
        self._room_locks: Dict[int, threading.RLock] = {}
        self._locks_lock = threading.Lock()  # 락 관리용 락
        
        # 현재 처리 중인 작업 추적
        self._pending_operations: Dict[int, Set[str]] = {}
    
    def _get_room_lock(self, room_id: int) -> threading.RLock:
        """방별 락을 가져옵니다."""
        with self._locks_lock:
            if room_id not in self._room_locks:
                self._room_locks[room_id] = threading.RLock()
                self._pending_operations[room_id] = set()
            return self._room_locks[room_id]
    
    def _add_pending_operation(self, room_id: int, operation: str) -> bool:
        """진행 중인 작업을 추가합니다."""
        with self._locks_lock:
            if room_id not in self._pending_operations:
                self._pending_operations[room_id] = set()
            
            # 동일한 작업이 이미 진행 중인지 확인
            if operation in self._pending_operations[room_id]:
                return False
            
            self._pending_operations[room_id].add(operation)
            return True
    
    def _remove_pending_operation(self, room_id: int, operation: str):
        """진행 중인 작업을 제거합니다."""
        with self._locks_lock:
            if room_id in self._pending_operations:
                self._pending_operations[room_id].discard(operation)
    
    def join_room_atomically(
        self, 
        db: Session, 
        room_id: int, 
        guest: Guest
    ) -> Tuple[bool, str, Optional[GameroomParticipant]]:
        """
        원자적 방 참가 처리
        
        Returns:
            (성공 여부, 메시지, 참가자 객체)
        """
        room_lock = self._get_room_lock(room_id)
        operation_key = f"join_{guest.guest_id}"
        
        # 중복 요청 방지
        if not self._add_pending_operation(room_id, operation_key):
            return False, "이미 처리 중인 요청입니다.", None
        
        try:
            with room_lock:
                return self._join_room_logic(db, room_id, guest)
        finally:
            self._remove_pending_operation(room_id, operation_key)
    
    def _join_room_logic(
        self, 
        db: Session, 
        room_id: int, 
        guest: Guest
    ) -> Tuple[bool, str, Optional[GameroomParticipant]]:
        """실제 방 참가 로직 (락 보호 하에 실행)"""
        try:
            # 1. 방 존재 여부 및 상태 확인
            room_query = """
                SELECT room_id, status, max_players, participant_count 
                FROM gamerooms 
                WHERE room_id = :room_id 
                FOR UPDATE
            """
            result = db.execute(text(room_query), {"room_id": room_id}).fetchone()
            
            if not result:
                return False, "존재하지 않는 방입니다.", None
            
            room_id_db, status, max_players, current_count = result
            
            # 2. 방 상태 검증
            if status != GameStatus.WAITING.value:
                return False, "대기 중인 방만 참가할 수 있습니다.", None
            
            # 3. 이미 참가했는지 확인
            existing_participant = db.execute(
                text("""
                    SELECT participant_id, left_at 
                    FROM gameroom_participants 
                    WHERE room_id = :room_id AND guest_id = :guest_id
                """),
                {"room_id": room_id, "guest_id": guest.guest_id}
            ).fetchone()
            
            if existing_participant:
                participant_id, left_at = existing_participant
                if left_at is None:
                    return False, "이미 참가한 방입니다.", None
                else:
                    # 재참가 처리
                    db.execute(
                        text("""
                            UPDATE gameroom_participants 
                            SET left_at = NULL, 
                                status = :status,
                                updated_at = :now
                            WHERE participant_id = :participant_id
                        """),
                        {
                            "participant_id": participant_id,
                            "status": ParticipantStatus.WAITING.value,
                            "now": datetime.now()
                        }
                    )
            else:
                # 4. 정원 확인 (동시성 고려)
                if current_count >= max_players:
                    return False, "방이 가득 찼습니다.", None
                
                # 5. 새 참가자 추가
                db.execute(
                    text("""
                        INSERT INTO gameroom_participants 
                        (room_id, guest_id, status, is_creator, joined_at, updated_at)
                        VALUES (:room_id, :guest_id, :status, false, :now, :now)
                    """),
                    {
                        "room_id": room_id,
                        "guest_id": guest.guest_id,
                        "status": ParticipantStatus.WAITING.value,
                        "now": datetime.now()
                    }
                )
            
            # 6. 참가자 수 업데이트 (트리거 대신 명시적 업데이트)
            db.execute(
                text("""
                    UPDATE gamerooms 
                    SET participant_count = (
                        SELECT COUNT(*) 
                        FROM gameroom_participants 
                        WHERE room_id = :room_id AND left_at IS NULL
                    ),
                    updated_at = :now
                    WHERE room_id = :room_id
                """),
                {"room_id": room_id, "now": datetime.now()}
            )
            
            # 7. 변경사항 커밋
            db.commit()
            
            # 8. 생성된 참가자 정보 반환
            participant = db.query(GameroomParticipant).filter(
                GameroomParticipant.room_id == room_id,
                GameroomParticipant.guest_id == guest.guest_id,
                GameroomParticipant.left_at.is_(None)
            ).first()
            
            return True, "방 참가 성공", participant
            
        except Exception as e:
            db.rollback()
            print(f"방 참가 오류: {str(e)}")
            return False, f"방 참가 실패: {str(e)}", None
    
    def leave_room_atomically(
        self, 
        db: Session, 
        room_id: int, 
        guest: Guest
    ) -> Tuple[bool, str]:
        """
        원자적 방 나가기 처리
        
        Returns:
            (성공 여부, 메시지)
        """
        room_lock = self._get_room_lock(room_id)
        operation_key = f"leave_{guest.guest_id}"
        
        if not self._add_pending_operation(room_id, operation_key):
            return False, "이미 처리 중인 요청입니다."
        
        try:
            with room_lock:
                return self._leave_room_logic(db, room_id, guest)
        finally:
            self._remove_pending_operation(room_id, operation_key)
    
    def _leave_room_logic(
        self, 
        db: Session, 
        room_id: int, 
        guest: Guest
    ) -> Tuple[bool, str]:
        """실제 방 나가기 로직"""
        try:
            # 1. 참가자 확인 및 상태 업데이트
            result = db.execute(
                text("""
                    UPDATE gameroom_participants 
                    SET left_at = :now, updated_at = :now
                    WHERE room_id = :room_id 
                    AND guest_id = :guest_id 
                    AND left_at IS NULL
                    RETURNING participant_id, is_creator
                """),
                {
                    "room_id": room_id,
                    "guest_id": guest.guest_id,
                    "now": datetime.now()
                }
            ).fetchone()
            
            if not result:
                return False, "참가하지 않은 방입니다."
            
            participant_id, is_creator = result
            
            # 2. 참가자 수 업데이트
            db.execute(
                text("""
                    UPDATE gamerooms 
                    SET participant_count = (
                        SELECT COUNT(*) 
                        FROM gameroom_participants 
                        WHERE room_id = :room_id AND left_at IS NULL
                    ),
                    updated_at = :now
                    WHERE room_id = :room_id
                """),
                {"room_id": room_id, "now": datetime.now()}
            )
            
            # 3. 방장이 나간 경우 권한 이양 또는 방 삭제
            if is_creator:
                self._handle_owner_leaving(db, room_id)
            
            db.commit()
            return True, "방 나가기 성공"
            
        except Exception as e:
            db.rollback()
            print(f"방 나가기 오류: {str(e)}")
            return False, f"방 나가기 실패: {str(e)}"
    
    def _handle_owner_leaving(self, db: Session, room_id: int):
        """방장이 나갔을 때의 처리"""
        # 남은 참가자 확인
        remaining_participants = db.execute(
            text("""
                SELECT guest_id, joined_at 
                FROM gameroom_participants 
                WHERE room_id = :room_id AND left_at IS NULL
                ORDER BY joined_at ASC
                LIMIT 1
            """),
            {"room_id": room_id}
        ).fetchone()
        
        if remaining_participants:
            # 가장 먼저 참가한 사람에게 방장 권한 이양
            new_owner_guest_id = remaining_participants[0]
            
            # 1. 새 방장의 참가자 정보 업데이트
            db.execute(
                text("""
                    UPDATE gameroom_participants 
                    SET is_creator = true, updated_at = :now
                    WHERE room_id = :room_id AND guest_id = :guest_id
                """),
                {
                    "room_id": room_id,
                    "guest_id": new_owner_guest_id,
                    "now": datetime.now()
                }
            )
            
            # 2. 방의 소유자 정보 업데이트
            db.execute(
                text("""
                    UPDATE gamerooms 
                    SET created_by = :new_owner, updated_at = :now
                    WHERE room_id = :room_id
                """),
                {
                    "room_id": room_id,
                    "new_owner": new_owner_guest_id,
                    "now": datetime.now()
                }
            )
        else:
            # 참가자가 없으면 방 삭제
            db.execute(
                text("DELETE FROM gamerooms WHERE room_id = :room_id"),
                {"room_id": room_id}
            )
    
    def cleanup_room_locks(self):
        """사용하지 않는 방 락 정리"""
        with self._locks_lock:
            # 진행 중인 작업이 없는 방의 락 제거
            rooms_to_cleanup = []
            for room_id, operations in self._pending_operations.items():
                if len(operations) == 0:
                    rooms_to_cleanup.append(room_id)
            
            for room_id in rooms_to_cleanup:
                if room_id in self._room_locks:
                    del self._room_locks[room_id]
                if room_id in self._pending_operations:
                    del self._pending_operations[room_id]


# 글로벌 인스턴스
room_state_manager = RoomStateManager()


def get_room_state_manager() -> RoomStateManager:
    """방 상태 관리자 인스턴스 반환"""
    return room_state_manager