from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import uuid

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus
from models.guest_model import Guest
from websocket.connection_manager import GameRoomWebSocketFacade
from repositories.guest_repository import GuestRepository
from repositories.game_log_repository import GameLogRepository
from services.game_state_service import GameStateService
from schemas.gameroom_actions_schema import JoinGameroomResponse

ws_manager = GameRoomWebSocketFacade()


class GameroomService:
    """
    게임룸 관련 비즈니스 로직을 처리하는 서비스 클래스.
    
    게임룸 생성, 참가, 퇴장, 게임 시작/종료 등의 기능을 제공하며,
    실시간 웹소켓 알림 기능도 포함합니다.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = GameroomRepository(db)
        self.guest_repository = GuestRepository(db)
        self.game_state_service = GameStateService(db)
        self.ws_manager = ws_manager
        if not hasattr(self.ws_manager.word_chain_engine, 'db') or self.ws_manager.word_chain_engine.db is None:
            self.ws_manager.word_chain_engine.db = db
            self.ws_manager.word_chain_engine.game_log_repository = GameLogRepository(db)

    def get_guest_by_cookie(self, request: Request) -> Guest:
        """쿠키에서 게스트 UUID를 추출하고 게스트 정보를 반환합니다."""
        guest_uuid_str = request.cookies.get("kkua_guest_uuid")
        if not guest_uuid_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="게스트 UUID 쿠키가 없습니다.",
            )

        try:
            guest_uuid = uuid.UUID(guest_uuid_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 UUID 형식입니다.",
            )

        guest = self.guest_repository.find_by_uuid(guest_uuid)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게스트를 찾을 수 없습니다.",
            )

        return guest

    def is_room_owner(self, room_id: int, guest_id: int) -> bool:
        """특정 게스트가 게임룸의 방장인지 확인합니다."""
        participant = self.repository.find_participant(room_id, guest_id)
        return participant is not None and participant.is_creator


    def list_gamerooms(self, status: Optional[str] = None, limit: int = 10, offset: int = 0) -> Tuple[List[Gameroom], int]:
        """게임룸 목록을 조회합니다."""
        filter_args = {}
        if status:
            filter_args["status"] = status

        return self.repository.find_all(
            limit=limit, offset=offset, filter_args=filter_args
        )

    def get_gameroom(self, room_id: int) -> Optional[Gameroom]:
        """게임룸 상세 정보를 조회합니다."""
        return self.repository.find_by_id(room_id)

    def create_gameroom(
        self, data: Dict[str, Any], guest_id: int
    ) -> Optional[Gameroom]:
        """게임룸을 생성하고 방장을 자동으로 참가자로 추가합니다."""
        try:
            room_data = data.copy()
            room_data["created_by"] = guest_id
            new_room = self.repository.create(room_data)

            self.repository.add_participant(
                room_id=new_room.room_id, guest_id=guest_id, is_creator=True
            )

            self.db.commit()
            self.db.refresh(new_room)

            return new_room

        except Exception as e:
            self.db.rollback()
            raise e

    def update_gameroom(self, room_id: int, data: Dict[str, Any]) -> Optional[Gameroom]:
        """게임룸 정보를 업데이트합니다."""
        return self.repository.update(room_id, data)

    def delete_gameroom(self, room_id: int) -> bool:
        """게임룸을 삭제합니다."""
        return self.repository.delete(room_id)

    async def join_gameroom(
        self, room_id: int, guest: Guest
    ) -> JoinGameroomResponse:
        """
        게임룸에 참가합니다.
        
        Args:
            room_id: 참가할 게임룸 ID
            guest: 참가할 게스트 객체
            
        Returns:
            JoinGameroomResponse: 참가 결과 정보
            
        Raises:
            HTTPException: 게임룸이 존재하지 않거나 참가 불가능한 경우
        """
        try:
            room = self.repository.find_by_id(room_id)
            if not room or room.status != GameStatus.WAITING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="게임룸 참가에 실패했습니다."
                )

            existing = self.repository.find_participant(room_id, guest.guest_id)
            if existing:
                return JoinGameroomResponse(
                    room_id=room_id, 
                    guest_id=guest.guest_id, 
                    message="이미 참가 중인 게임룸입니다."
                )

            if room.participant_count >= room.max_players:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="게임룸이 가득 찼습니다."
                )

            participant = self.repository.add_participant(room_id, guest.guest_id)
            
            self.db.commit()
            self.db.refresh(participant)

            if self.ws_manager:
                asyncio.create_task(
                    self.ws_manager.broadcast_room_update(
                        room_id,
                        "player_joined",
                        {
                            "guest_id": guest.guest_id,
                            "nickname": guest.nickname,
                            "joined_at": datetime.now().isoformat(),
                            "is_creator": False,
                        },
                    )
                )

            return JoinGameroomResponse(
                room_id=room_id, 
                guest_id=guest.guest_id, 
                message="게임룸에 참가했습니다."
            )

        except Exception as e:
            self.db.rollback()
            raise e

    def leave_gameroom(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임룸을 떠납니다."""
        try:
            room = self.repository.find_by_id(room_id)
            participant = self.repository.find_participant(room_id, guest.guest_id)

            if not room or not participant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="게임룸 퇴장에 실패했습니다."
                )

            self.repository.remove_participant(room_id, guest.guest_id)

            if participant.is_creator:
                remaining = self.repository.find_room_participants(room_id)
                if remaining:
                    new_host = remaining[0]
                    new_host.is_creator = True
                    room.created_by = new_host.guest_id
                    
                    if self.ws_manager:
                        asyncio.create_task(
                            self.ws_manager.broadcast_room_update(
                                room_id,
                                "host_changed",
                                {
                                    "new_host_id": new_host.guest_id,
                                    "new_host_nickname": new_host.guest.nickname if new_host.guest else f"게스트_{new_host.guest_id}",
                                    "message": f"{new_host.guest.nickname if new_host.guest else f'게스트_{new_host.guest_id}'}님이 새로운 방장이 되었습니다.",
                                },
                            )
                        )
                else:
                    # 남은 참가자가 없으면 게임룸 종료
                    room.status = GameStatus.FINISHED

            self.db.commit()

            # 웹소켓 이벤트 발송 (참가자 퇴장)
            if self.ws_manager:
                asyncio.create_task(
                    self.ws_manager.broadcast_room_update(
                        room_id,
                        "player_left",
                        {
                            "guest_id": guest.guest_id,
                            "nickname": guest.nickname,
                            "left_at": datetime.now().isoformat(),
                        },
                    )
                )

            return {"message": "게임룸에서 퇴장했습니다."}

        except Exception as e:
            self.db.rollback()
            raise e

    def toggle_ready_status(self, room_id: int, guest: Guest) -> Optional[str]:
        """준비 상태를 토글합니다."""
        try:
            participant = self.repository.find_participant(room_id, guest.guest_id)
            if not participant:
                return None

            # 방장은 항상 READY 상태
            if participant.is_creator:
                return ParticipantStatus.READY.value

            # 준비 상태 토글
            new_status = ParticipantStatus.WAITING
            if participant.status == ParticipantStatus.WAITING.value:
                new_status = ParticipantStatus.READY

            updated = self.repository.update_participant_status(
                room_id, participant.participant_id, new_status.value
            )
            return updated.status if updated else None

        except Exception as e:
            self.db.rollback()
            raise e

    async def start_game(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임을 시작합니다. 방장만 게임을 시작할 수 있습니다."""
        # 게임 시작 가능 여부 확인
        can_start, error_message = self.game_state_service.can_start_game(room_id, guest.guest_id)
        if not can_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # 게임 시작
        success = self.game_state_service.start_game(room_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 시작에 실패했습니다."
            )

        # Redis 기반 게임 시스템 초기화
        try:
            from services.redis_game_service import get_redis_game_service
            redis_game = await get_redis_game_service()
            
            # 참가자 목록 준비
            participants = self.repository.find_room_participants(room_id)
            participant_data = [
                {
                    "guest_id": p.guest.guest_id,
                    "nickname": p.guest.nickname,
                    "is_creator": p.guest.guest_id == p.gameroom.created_by,
                }
                for p in participants if p.left_at is None
            ]
            
            # 게임룸 정보에서 설정 가져오기
            room = self.repository.find_by_id(room_id)
            game_settings = {
                'turn_time_limit': 30,
                'max_rounds': room.max_rounds if room else 10,
                'word_min_length': 2,
                'use_items': True
            }
            
            # Redis에 게임 생성 및 시작
            await redis_game.create_game(room_id, participant_data, game_settings)
            await redis_game.start_game(room_id, "끝말잇기")
            
            print(f"🎮 Redis 게임 초기화 완료: room_id={room_id}")
            
        except Exception as e:
            print(f"❌ Redis 게임 초기화 실패: {e}")
            # Redis 실패 시 기존 메모리 기반 시스템으로 fallback
            if self.ws_manager:
                participants = self.repository.find_room_participants(room_id)
                participant_data = [
                    {
                        "guest_id": p.guest.guest_id,
                        "nickname": p.guest.nickname,
                        "status": p.status.value if hasattr(p.status, "value") else p.status,
                        "is_creator": p.guest.guest_id == p.gameroom.created_by,
                    }
                    for p in participants if p.left_at is None
                ]
                room = self.repository.find_by_id(room_id)
                max_rounds = room.max_rounds if room else 10
                self.ws_manager.initialize_word_chain_game(room_id, participant_data, max_rounds)
                self.ws_manager.start_word_chain_game(room_id, "끝말잇기")

        # 웹소켓 이벤트 발송 (게임 시작) - Redis 성공/실패 관계없이 실행
        print(f"🎮 게임 시작 WebSocket 브로드캐스트 시작: room_id={room_id}")
        try:
            await self.ws_manager.broadcast_room_update(
                room_id,
                "game_started",
                {
                    "room_id": room_id,
                    "started_at": datetime.now().isoformat(),
                    "message": "게임이 시작되었습니다!",
                },
            )
            print(f"✅ 게임 시작 WebSocket 브로드캐스트 완료: room_id={room_id}")

            # 끝말잇기 게임 상태 브로드캐스트
            await self.ws_manager.broadcast_word_chain_state(room_id)

            # 첫 턴 타이머 시작
            await self.ws_manager.start_turn_timer(room_id, 15)
        except Exception as e:
            print(f"❌ WebSocket 브로드캐스트 실패: {e}")
            # WebSocket 실패해도 게임 시작은 성공으로 처리

        return {"message": "게임이 시작되었습니다!", "status": "PLAYING"}

    def end_game(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임을 종료하고 결과를 생성합니다."""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 게임 종료 처리
        success = self.game_state_service.end_game(room_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 종료에 실패했습니다."
            )

        # 게임룸 상태를 FINISHED로 변경
        room.status = GameStatus.FINISHED.value
        room.ended_at = datetime.now()
        self.db.commit()

        # 승자 결정 (간단한 로직 - 첫 번째 참가자)
        participants = self.repository.find_room_participants(room_id)
        winner = None
        if participants and participants[0].guest:
            winner = participants[0].guest

        # 웹소켓 이벤트 발송 (게임 종료 및 결과 페이지 이동 알림)
        if self.ws_manager:
            from schemas.gameroom_ws_schema import GameEndedMessage
            
            end_message = GameEndedMessage(
                room_id=room_id,
                winner_id=winner.guest_id if winner else None,
                winner_name=winner.nickname if winner else None,
                message=f"게임이 종료되었습니다! {winner.nickname if winner else '무승부'}",
                result_available=True,
                timestamp=datetime.now()
            )
            
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "game_ended",
                    end_message.dict(),
                )
            )

        return {
            "message": f"게임이 종료되었습니다! 승자: {winner.nickname if winner else '무승부'}",
            "status": "FINISHED",
            "winner": winner.nickname if winner else None,
            "result_available": True
        }

    def get_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """게임룸 참가자 목록을 조회합니다."""
        return self.repository.get_participants(room_id)

    def update_participant_status(
        self, room_id: int, guest_id: int, status: str
    ) -> Dict[str, str]:
        """참가자 상태를 업데이트합니다. (웹소켓을 통해 호출)"""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다",
            )

        # 참가자 조회
        participant = self.repository.find_participant(room_id, guest_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 참가자를 찾을 수 없습니다",
            )

        # 진행 중인 게임에서는 상태 변경 불가
        if room.status == GameStatus.PLAYING and status.upper() != "PLAYING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 진행 중에는 상태를 변경할 수 없습니다",
            )

        # 상태 업데이트
        updated_participant = self.repository.update_participant_status(
            participant.id, status.upper()
        )

        # 웹소켓으로 상태 변경 알림 (ws_manager 유효성 검사 추가)
        if self.ws_manager:
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "status_changed",
                    {"guest_id": guest_id, "status": updated_participant.status.value},
                )
            )

        return {"detail": "참가자 상태가 업데이트되었습니다."}

    async def toggle_ready_status_with_ws(self, room_id: int, guest: Guest) -> Dict[str, Any]:
        """참가자의 준비 상태를 토글합니다. (웹소켓 알림 포함)"""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다.",
            )

        # 참가자 조회
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant or participant.left_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 게임룸에 참가 중이 아닙니다.",
            )

        # 게임 상태 확인
        if room.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대기 중인 게임방에서만 준비 상태를 변경할 수 있습니다.",
            )

        # 방장 확인 - 방장은 항상 준비 상태
        if self.is_room_owner(room_id, guest.guest_id):
            return {
                "status": ParticipantStatus.READY.value,
                "message": "방장은 항상 준비 상태입니다.",
                "is_ready": True,
            }

        # 현재 상태 확인 및 새 상태 설정
        current_status = participant.status
        
        new_status = None
        if (
            current_status == ParticipantStatus.WAITING.value
            or current_status == ParticipantStatus.WAITING
        ):
            new_status = ParticipantStatus.READY.value
            is_ready = True
            message = "준비 완료!"
        else:
            new_status = ParticipantStatus.WAITING.value
            is_ready = False
            message = "준비 취소!"

        # 상태 업데이트
        result = self.repository.update_participant_status(
            room.room_id, participant.participant_id, new_status
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="참가자 상태 업데이트에 실패했습니다.",
            )

        # 웹소켓 이벤트 발송 (참가자 상태 변경)
        if self.ws_manager:
            await self.ws_manager.broadcast_ready_status(
                room_id, guest.guest_id, is_ready, guest.nickname
            )

        return {"status": new_status, "message": message, "is_ready": is_ready}

    def check_active_game(self, guest_uuid_str: str = None) -> Dict[str, Any]:
        """유저가 현재 참여 중인 게임이 있는지 확인합니다."""
        if guest_uuid_str:
            # URL 파라미터로 UUID가 제공된 경우
            try:
                guest_uuid = uuid.UUID(guest_uuid_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 UUID 형식입니다.",
                )
        else:
            return {"has_active_game": False, "room_id": None}

        # UUID로 게스트 조회
        guest = self.guest_repository.find_by_uuid(guest_uuid)
        if not guest:
            return {"has_active_game": False, "room_id": None}

        # 활성화된 게임 확인
        should_redirect, active_room_id = self.guest_repository.check_active_game(
            guest.guest_id
        )

        return {"has_active_game": should_redirect, "room_id": active_room_id}

    def check_if_owner(self, room_id: int, guest: Guest) -> Dict[str, bool]:
        """현재 게스트가 특정 게임룸의 방장인지 확인합니다."""
        try:
            # 게임룸 조회
            room = self.repository.find_by_id(room_id)
            if not room:
                return {"is_owner": False}

            # 방장 여부 확인
            is_owner = self.is_room_owner(room_id, guest.guest_id)

            return {"is_owner": is_owner}
        except HTTPException:
            return {"is_owner": False}
    
    def get_game_result(self, room_id: int, guest: Guest) -> Dict[str, Any]:
        """게임 결과를 조회합니다."""
        from schemas.gameroom_schema import GameResultResponse, PlayerGameResult, WordChainEntry
        
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 참가자 권한 확인 (게임이 끝나지 않아도 결과 조회 허용)
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게임 참가자만 결과를 조회할 수 있습니다"
            )
        
        # 게임 로그 조회
        game_log_repo = GameLogRepository(self.db)
        game_log = game_log_repo.find_game_log_by_room_id(room_id)
        
        if game_log:
            # 실제 게임 데이터 사용
            players_stats = game_log_repo.get_player_stats_by_game_log(game_log.id)
            word_entries = game_log_repo.get_word_entries_by_game_log(game_log.id)
            
            # 플레이어 통계 데이터 변환
            players_data = []
            for stats in players_stats:
                if stats.player:
                    players_data.append(PlayerGameResult(
                        guest_id=stats.player_id,
                        nickname=stats.player.nickname,
                        words_submitted=stats.words_submitted,
                        total_score=stats.total_score,
                        avg_response_time=stats.avg_response_time or 0.0,
                        longest_word=stats.longest_word or "단어없음",
                        rank=stats.rank
                    ))
            
            # 단어 엔트리 데이터 변환
            used_words_data = []
            for entry in word_entries:
                if entry.player:
                    used_words_data.append(WordChainEntry(
                        word=entry.word,
                        player_id=entry.player_id,
                        player_name=entry.player.nickname,
                        timestamp=entry.submitted_at,
                        response_time=entry.response_time or 0.0
                    ))
            
            # 승자 결정
            winner = None
            if game_log.winner:
                winner_stats = next((p for p in players_data if p.guest_id == game_log.winner_id), None)
                winner = winner_stats
            elif players_data:
                winner = players_data[0]  # 순위 1위
                
            # 게임 지속 시간
            game_duration = game_log.get_game_duration_formatted()
            
            # 실제 통계 사용
            total_rounds = game_log.total_rounds
            total_words = game_log.total_words
            average_response_time = game_log.average_response_time or 0.0
            longest_word = game_log.longest_word or "없음"
            fastest_response = game_log.fastest_response_time or 0.0
            slowest_response = game_log.slowest_response_time or 0.0
            mvp_name = winner.nickname if winner else "없음"
            
        else:
            # 게임 로그가 없는 경우 목업 데이터 사용
            participants = self.repository.find_room_participants(room_id)
            
            players_data = []
            used_words_data = []
            
            # 플레이어별 통계 생성
            for i, p in enumerate(participants):
                if not p.guest:
                    continue
                    
                # 목업 통계 데이터
                words_count = max(1, 8 - i)  # 다양한 단어 수
                avg_time = 2.5 + (i * 0.7)  # 다양한 응답시간
                score = words_count * 3 + (10 - i)  # 점수 계산
                
                players_data.append(PlayerGameResult(
                    guest_id=p.guest.guest_id,
                    nickname=p.guest.nickname,
                    words_submitted=words_count,
                    total_score=score,
                    avg_response_time=round(avg_time, 1),
                    longest_word=f"프로그래밍{i}" if i == 0 else f"단어{i}",
                    rank=i + 1
                ))
            
            # 사용된 단어 목업 데이터
            sample_words = ["사과", "과일", "일기", "기술", "컴퓨터", "터미널", "널뛰기", "기계학습"]
            for i, word in enumerate(sample_words[:min(len(sample_words), len(participants) * 2)]):
                player_idx = i % len(participants)
                if participants[player_idx].guest:
                    used_words_data.append(WordChainEntry(
                        word=word,
                        player_id=participants[player_idx].guest.guest_id,
                        player_name=participants[player_idx].guest.nickname,
                        timestamp=datetime.now(),
                        response_time=round(2.0 + (i * 0.3), 1)
                    ))
            
            # 승자 결정 (첫 번째 플레이어)
            winner = players_data[0] if players_data else None
            
            # 목업 통계
            game_duration = "5분 23초"
            total_rounds = room.max_rounds or 10
            total_words = len(used_words_data)
            average_response_time = 4.2
            longest_word = "프로그래밍"
            fastest_response = 2.1
            slowest_response = 6.2
            mvp_name = winner.nickname if winner else "없음"
        if room.started_at and room.ended_at:
            duration = room.ended_at - room.started_at
            duration_str = f"{duration.seconds // 60}분 {duration.seconds % 60}초"
        else:
            duration_str = "5분 23초"  # 기본값
        
        # 통계 계산
        total_words = len(used_words_data)
        avg_response_time = sum(w.response_time or 0 for w in used_words_data) / max(total_words, 1)
        fastest_response = min((w.response_time or 10 for w in used_words_data), default=2.1)
        slowest_response = max((w.response_time or 0 for w in used_words_data), default=6.2)
        longest_word = max((w.word for w in used_words_data), key=len, default="")
        
        result = GameResultResponse(
            room_id=room_id,
            winner_id=winner.guest_id if winner else None,
            winner_name=winner.nickname if winner else None,
            players=players_data,
            used_words=used_words_data,
            total_rounds=room.max_rounds,
            game_duration=duration_str,
            total_words=total_words,
            average_response_time=round(avg_response_time, 1),
            longest_word=longest_word,
            fastest_response=round(fastest_response, 1),
            slowest_response=round(slowest_response, 1),
            mvp_id=winner.guest_id if winner else None,
            mvp_name=winner.nickname if winner else None,
            started_at=room.started_at,
            ended_at=room.ended_at
        )
        
        return result
