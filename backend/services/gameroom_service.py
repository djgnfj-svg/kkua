from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import uuid
import logging

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus
from models.guest_model import Guest
from websocket.connection_manager import GameRoomWebSocketFacade
from repositories.guest_repository import GuestRepository
from repositories.game_log_repository import GameLogRepository
from services.game_state_service import GameStateService
from services.game_data_persistence_service import GameDataPersistenceService
from schemas.gameroom_actions_schema import JoinGameroomResponse

ws_manager = GameRoomWebSocketFacade()
logger = logging.getLogger(__name__)


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
        self.background_tasks = set()  # 메모리 누수 방지를 위한 백그라운드 태스크 추적
        if not hasattr(self.ws_manager.word_chain_engine, 'db') or self.ws_manager.word_chain_engine.db is None:
            self.ws_manager.word_chain_engine.db = db
            self.ws_manager.word_chain_engine.game_log_repository = GameLogRepository(db)
    
    def create_background_task(self, coro, name: str = None):
        """메모리 누수 방지를 위한 안전한 백그라운드 태스크 생성"""
        task = asyncio.create_task(coro, name=name)
        self.background_tasks.add(task)
        task.add_done_callback(lambda t: self.background_tasks.discard(t))
        return task

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
                self.create_background_task(
                    self.ws_manager.broadcast_room_update(
                        room_id,
                        "player_joined",
                        {
                            "guest_id": guest.guest_id,
                            "nickname": guest.nickname,
                            "joined_at": datetime.now().isoformat(),
                            "is_creator": False,
                        },
                    ),
                    name=f"player_joined_broadcast_{room_id}_{guest.guest_id}"
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
                        self.create_background_task(
                            self.ws_manager.broadcast_room_update(
                                room_id,
                                "host_changed",
                                {
                                    "new_host_id": new_host.guest_id,
                                    "new_host_nickname": new_host.guest.nickname if new_host.guest else f"게스트_{new_host.guest_id}",
                                    "message": f"{new_host.guest.nickname if new_host.guest else f'게스트_{new_host.guest_id}'}님이 새로운 방장이 되었습니다.",
                                },
                            ),
                            name=f"host_changed_broadcast_{room_id}_{new_host.guest_id}"
                        )
                else:
                    # 남은 참가자가 없으면 게임룸 종료
                    room.status = GameStatus.FINISHED

            self.db.commit()

            # 웹소켓 이벤트 발송 (참가자 퇴장)
            if self.ws_manager:
                self.create_background_task(
                    self.ws_manager.broadcast_room_update(
                        room_id,
                        "player_left",
                        {
                            "guest_id": guest.guest_id,
                            "nickname": guest.nickname,
                            "left_at": datetime.now().isoformat(),
                        },
                    ),
                    name=f"player_left_broadcast_{room_id}_{guest.guest_id}"
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
        
        # 게임룸 상태를 PLAYING으로 변경
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다."
            )
        
        room.status = GameStatus.PLAYING.value
        room.started_at = datetime.now()
        self.db.commit()
        
        # 게임 시작
        success = self.game_state_service.start_game(room_id)
        if not success:
            # 상태 롤백
            room.status = GameStatus.WAITING.value
            room.started_at = None
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 시작에 실패했습니다."
            )

        # 즉시 게임 시작 WebSocket 브로드캐스트 (빠른 응답)
        try:
            await self.ws_manager.broadcast_to_room(room_id, {
                'type': 'game_started',
                'room_id': room_id,
                'message': '🎮 게임이 시작되었습니다! 게임 페이지로 이동합니다.',
                'started_at': datetime.now().isoformat(),
                'status': 'playing'
            })
            logger.info(f"즉시 게임 시작 WebSocket 브로드캐스트 완료: room_id={room_id}")
        except Exception as e:
            logger.error(f"즉시 게임 시작 WebSocket 브로드캐스트 실패: {e}")

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
            
            if not participant_data:
                raise Exception("참가자가 없습니다.")
            
            # 게임룸 정보에서 설정 가져오기
            game_settings = {
                'turn_time_limit': 30,
                'max_rounds': room.max_rounds if room else 10,
                'word_min_length': 2,
                'use_items': True
            }
            
            # 게임 모드 설정이 있으면 추가
            game_mode_config = None
            if room.game_mode_config:
                game_mode_config = room.game_mode_config
                # 게임 모드 설정으로 기본 설정 덮어쓰기
                if 'settings' in game_mode_config:
                    mode_settings = game_mode_config['settings']
                    if 'turn_time_limit' in mode_settings:
                        game_settings['turn_time_limit'] = mode_settings['turn_time_limit']
                    if 'max_rounds' in mode_settings:
                        game_settings['max_rounds'] = mode_settings['max_rounds']
                    if 'min_word_length' in mode_settings:
                        game_settings['word_min_length'] = mode_settings['min_word_length']
                    if 'score_multiplier' in mode_settings:
                        game_settings['score_multiplier'] = mode_settings['score_multiplier']
                    if 'special_rules' in mode_settings:
                        game_settings['special_rules'] = mode_settings['special_rules']
            
            # Redis에 게임 생성 및 시작 (게임 모드 설정 전달)
            await redis_game.create_game(room_id, participant_data, game_settings, game_mode_config)
            await redis_game.start_game(room_id, "끝말잇기")
            
            logger.info(f"Redis 게임 초기화 완료: room_id={room_id}, participants={len(participant_data)}")
            
        except Exception as e:
            logger.error(f"Redis 게임 초기화 실패: {e}")
            # Redis 실패 시 DB 상태 롤백
            room.status = GameStatus.WAITING.value
            room.started_at = None
            self.db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="게임 초기화에 실패했습니다."
            )

        # 게임 시작 WebSocket 브로드캐스트 (Redis와 별도로 전송)
        try:
            await self.ws_manager.broadcast_to_room(room_id, {
                'type': 'game_started',
                'room_id': room_id,
                'message': '🎮 게임이 시작되었습니다! 게임 페이지로 이동합니다.',
                'started_at': datetime.now().isoformat(),
                'status': 'playing'
            })
            logger.info(f"게임 시작 WebSocket 브로드캐스트 완료: room_id={room_id}")
        except Exception as e:
            logger.error(f"게임 시작 WebSocket 브로드캐스트 실패: {e}")
            # WebSocket 실패해도 게임 시작은 성공으로 처리

        return {"message": "게임이 시작되었습니다!", "status": "PLAYING"}

    async def end_game(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임을 종료하고 결과를 생성합니다."""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 방장인지 확인
        if room.created_by != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방장만 게임을 종료할 수 있습니다."
            )
        
        # Redis 게임 상태 종료
        try:
            from services.redis_game_service import get_redis_game_service
            redis_game = await get_redis_game_service()
            await redis_game.end_game(room_id)
            await redis_game.cleanup_game(room_id)
            logger.info(f"Redis 게임 종료 완료: room_id={room_id}")
        except Exception as e:
            logger.error(f"Redis 게임 종료 실패: {e}")
            # Redis 실패해도 계속 진행

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

        # Redis에서 플레이어 통계 가져오기 (승자 결정)
        winner = None
        game_log = None
        try:
            from services.redis_game_service import get_redis_game_service
            redis_game = await get_redis_game_service()
            player_stats = await redis_game.get_all_player_stats(room_id)
            
            if player_stats:
                # 최고 점수 플레이어를 승자로 선정
                winner_stat = max(player_stats, key=lambda x: x['score'])
                # 승자의 정보를 가져오기 위해 guest_repository 사용
                winner = self.guest_repository.find_by_id(winner_stat['guest_id'])
            
            # 게임 데이터를 PostgreSQL에 저장
            persistence_service = GameDataPersistenceService(self.db, redis_game)
            game_log = await persistence_service.save_game_data(
                room_id=room_id,
                winner_id=winner.guest_id if winner else None,
                end_reason="ended_by_host"
            )
            logger.info(f"게임 데이터 PostgreSQL 저장 완료: game_log_id={game_log.id if game_log else 'None'}")
            
            # Redis 게임 데이터는 PostgreSQL 저장 후 지연 정리 (30분 후)
            self.create_background_task(
                self._delayed_cleanup(redis_game, room_id, delay_minutes=30),
                name=f"delayed_cleanup_{room_id}"
            )
        except Exception as e:
            logger.error(f"승자 결정 및 데이터 저장 실패: {e}")
            # 기본적으로 방장을 승자로 설정
            winner = guest

        # WebSocket으로 게임 종료 알림
        try:
            await self.ws_manager.broadcast_to_room(room_id, {
                'type': 'game_ended_by_host',
                'room_id': room_id,
                'ended_by_id': guest.guest_id,
                'ended_by_nickname': guest.nickname,
                'winner_id': winner.guest_id if winner else None,
                'winner_nickname': winner.nickname if winner else None,
                'message': f'🏁 게임이 종료되었습니다! 승자: {winner.nickname if winner else "무승부"}',
                'result_available': True,
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"게임 종료 WebSocket 브로드캐스트 완료: room_id={room_id}")
        except Exception as e:
            logger.error(f"WebSocket 브로드캐스트 실패: {e}")

        return {
            "message": "게임이 종료되었습니다!", 
            "status": "FINISHED",
            "winner": winner.nickname if winner else None,
            "result_available": True
        }

    async def complete_game(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임을 완료합니다. 모든 참가자가 완료할 수 있습니다 (테스트용)."""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 참가자인지 확인 (모든 참가자가 완료 가능)
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게임 참가자만 게임을 완료할 수 있습니다."
            )
        
        # 게임이 진행 중인지 확인
        if room.status != GameStatus.PLAYING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="진행 중인 게임만 완료할 수 있습니다."
            )
        
        # Redis 게임 상태 종료
        try:
            from services.redis_game_service import get_redis_game_service
            redis_game = await get_redis_game_service()
            await redis_game.end_game(room_id)
            logger.info(f"Redis 게임 완료 처리: room_id={room_id}")
        except Exception as e:
            logger.error(f"Redis 게임 완료 처리 실패: {e}")
            # Redis 실패해도 계속 진행

        # 게임 완료 처리
        success = self.game_state_service.end_game(room_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 완료 처리에 실패했습니다."
            )

        # 게임룸 상태를 FINISHED로 변경
        room.status = GameStatus.FINISHED.value
        room.ended_at = datetime.now()
        self.db.commit()

        # Redis에서 플레이어 통계 가져오기 (승자 결정)
        winner = None
        game_log = None
        try:
            from services.redis_game_service import get_redis_game_service
            redis_game = await get_redis_game_service()
            player_stats = await redis_game.get_all_player_stats(room_id)
            
            if player_stats:
                # 최고 점수 플레이어를 승자로 선정
                winner_stat = max(player_stats, key=lambda x: x['score'])
                # 승자의 정보를 가져오기 위해 guest_repository 사용
                winner = self.guest_repository.find_by_id(winner_stat['guest_id'])
            
            # 게임 데이터를 PostgreSQL에 저장
            persistence_service = GameDataPersistenceService(self.db, redis_game)
            game_log = await persistence_service.save_game_data(
                room_id=room_id,
                winner_id=winner.guest_id if winner else None,
                end_reason="manual_complete"
            )
            logger.info(f"게임 데이터 PostgreSQL 저장 완료: game_log_id={game_log.id if game_log else 'None'}")
            
            # Redis 게임 데이터는 PostgreSQL 저장 후 지연 정리 (30분 후)
            self.create_background_task(
                self._delayed_cleanup(redis_game, room_id, delay_minutes=30),
                name=f"delayed_cleanup_{room_id}"
            )
        except Exception as e:
            logger.error(f"승자 결정 및 데이터 저장 실패: {e}")
            # 기본적으로 요청한 사용자를 승자로 설정
            winner = guest

        # WebSocket으로 게임 완료 알림 (모달 표시용)
        try:
            await self.ws_manager.broadcast_to_room(room_id, {
                'type': 'game_completed',
                'room_id': room_id,
                'completed_by_id': guest.guest_id,
                'completed_by_nickname': guest.nickname,
                'winner_id': winner.guest_id if winner else None,
                'winner_nickname': winner.nickname if winner else None,
                'message': f'🎉 게임이 완료되었습니다! 승자: {winner.nickname if winner else "무승부"}',
                'show_modal': True,
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"게임 완룼 WebSocket 브로드캐스트 완료: room_id={room_id}")
        except Exception as e:
            logger.error(f"WebSocket 브로드캐스트 실패: {e}")

        return {
            "message": "게임이 완료되었습니다!", 
            "status": "COMPLETED",
            "winner": winner.nickname if winner else None,
            "show_modal": True
        }

    async def _delayed_cleanup(self, redis_game, room_id: int, delay_minutes: int = 30):
        """Redis 게임 데이터를 지연 정리합니다."""
        try:
            import asyncio
            await asyncio.sleep(delay_minutes * 60)  # 분을 초로 변환
            await redis_game.cleanup_game(room_id)
            logger.info(f"Redis 게임 데이터 지연 정리 완료: room_id={room_id}, delay={delay_minutes}분")
        except Exception as e:
            logger.error(f"Redis 게임 데이터 지연 정리 실패: {e}")

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
            self.create_background_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "status_changed",
                    {"guest_id": guest_id, "status": updated_participant.status.value},
                ),
                name=f"status_changed_broadcast_{room_id}_{guest_id}"
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
    
    async def get_game_result(self, room_id: int, guest: Guest) -> Dict[str, Any]:
        """게임 결과를 조회합니다."""
        # 권한 검증
        room, participant = self._validate_game_result_access(room_id, guest)
        
        # PostgreSQL에서 저장된 결과 조회
        saved_result = await self._get_saved_game_result(room_id)
        if saved_result:
            return saved_result
        
        # Redis에서 실시간 데이터 조회
        redis_result = await self._get_redis_game_result(room_id)
        if redis_result:
            return redis_result
        
        # 데모 데이터 또는 오류 응답
        return await self._get_fallback_game_result(room_id, room)
    
    def _validate_game_result_access(self, room_id: int, guest: Guest):
        """게임 결과 조회 권한을 검증합니다."""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다"
            )
        
        # 참가자 권한 확인
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게임 참가자만 결과를 조회할 수 있습니다"
            )
        
        return room, participant
    
    async def _get_saved_game_result(self, room_id: int):
        """PostgreSQL에서 저장된 게임 결과를 조회합니다."""
        try:
            from services.redis_game_service import get_redis_game_service
            from schemas.gameroom_schema import GameResultResponse
            
            redis_game = await get_redis_game_service()
            persistence_service = GameDataPersistenceService(self.db, redis_game)
            
            saved_game_result = await persistence_service.get_game_result_data(room_id)
            if saved_game_result:
                logger.info("PostgreSQL에서 저장된 게임 결과 발견")
                return GameResultResponse(**saved_game_result)
            
            return None
        except Exception as e:
            logger.error(f"저장된 게임 결과 조회 실패: {e}")
            return None
    
    async def _get_redis_game_result(self, room_id: int):
        """Redis에서 실시간 게임 결과를 조회합니다."""
        try:
            from services.redis_game_service import get_redis_game_service
            from schemas.gameroom_schema import GameResultResponse, PlayerGameResult, WordChainEntry
            
            redis_game = await get_redis_game_service()
            
            # Redis에서 게임 데이터 조회
            game_state = await redis_game.get_game_state(room_id)
            all_player_stats = await redis_game.get_all_player_stats(room_id)
            word_entries = await redis_game.get_word_entries(room_id)
            game_stats = await redis_game.get_game_stats(room_id)
            
            logger.debug(f"Redis 데이터 조회 결과: game_state={bool(game_state)}, "
                        f"player_stats={len(all_player_stats) if all_player_stats else 0}, "
                        f"word_entries={len(word_entries) if word_entries else 0}")
            
            # 게임 상태가 있지만 플레이어 통계가 없는 경우 (빈 게임)
            if game_state and not all_player_stats:
                logger.warning(f"게임 상태는 있지만 플레이어 통계가 없음: room_id={room_id}")
                # 기본 플레이어 데이터 생성 시도
                participants = game_state.get('participants', [])
                if participants:
                    logger.info("참가자 정보로부터 기본 플레이어 데이터 생성")
                    default_players = []
                    for i, participant in enumerate(participants):
                        default_players.append({
                            'guest_id': participant['guest_id'],
                            'nickname': participant['nickname'],
                            'words_submitted': 0,
                            'score': 0,
                            'average_response_time': 0.0,
                            'longest_word': '',
                            'fastest_response': None,
                            'slowest_response': None
                        })
                    all_player_stats = default_players
            
            if not (game_state and all_player_stats):
                logger.warning("Redis에 게임 데이터 없음")
                return None
            
            logger.info("Redis에서 게임 데이터 발견 - 결과 생성 중")
            
            # 플레이어 데이터 변환 및 정렬
            players_data = self._convert_player_stats(all_player_stats)
            
            # 데이터 완정성 검증: 모든 플레이어의 점수가 0이고 단어가 없으면 처리 중일 가능성
            all_scores_zero = all(player.total_score == 0 for player in players_data)
            no_words = not word_entries or len(word_entries) == 0
            game_has_used_words = game_state.get('used_words', [])
            
            if all_scores_zero and no_words and game_has_used_words:
                logger.warning(f"게임 데이터가 아직 완전히 처리되지 않음: room_id={room_id}")
                # 데이터 처리가 완료되지 않았을 수 있음을 알리는 표시 추가
                for player in players_data:
                    player.total_score = -1  # 특별한 값으로 처리 중임을 표시
            
            # 단어 체인 데이터 변환
            used_words_data = self._convert_word_entries(word_entries or [])
            
            # 게임 결과 생성
            return self._build_game_result_response(
                room_id, game_state, players_data, used_words_data, 
                word_entries or [], game_stats or {}
            )
            
        except Exception as e:
            logger.error(f"Redis 게임 데이터 조회 실패: {e}")
            return None
    
    def _convert_player_stats(self, all_player_stats):
        """플레이어 통계를 변환하고 정렬합니다."""
        from schemas.gameroom_schema import PlayerGameResult
        
        players_data = []
        for player_stats in all_player_stats:
            players_data.append(PlayerGameResult(
                guest_id=player_stats['guest_id'],
                nickname=player_stats['nickname'],
                words_submitted=player_stats.get('words_submitted', 0),
                total_score=player_stats.get('score', 0),
                avg_response_time=player_stats.get('average_response_time', 0.0),
                longest_word=player_stats.get('longest_word', ''),
                rank=1  # 임시 순위
            ))
        
        # 점수 기준으로 정렬 및 순위 재계산
        players_data.sort(key=lambda x: x.total_score, reverse=True)
        for rank, player in enumerate(players_data, 1):
            player.rank = rank
        
        return players_data
    
    def _convert_word_entries(self, word_entries):
        """단어 엔트리를 변환합니다."""
        from schemas.gameroom_schema import WordChainEntry
        
        used_words_data = []
        for word_entry in word_entries:
            used_words_data.append(WordChainEntry(
                word=word_entry['word'],
                player_id=word_entry['player_id'],
                player_name=word_entry['player_nickname'],
                timestamp=datetime.fromisoformat(word_entry['submitted_at']) if word_entry.get('submitted_at') else datetime.now(),
                response_time=word_entry.get('response_time', 0.0)
            ))
        
        return used_words_data
    
    def _build_game_result_response(self, room_id, game_state, players_data, used_words_data, word_entries, game_stats):
        """게임 결과 응답을 생성합니다."""
        from schemas.gameroom_schema import GameResultResponse
        
        winner = players_data[0] if players_data else None
        
        return GameResultResponse(
            room_id=room_id,
            winner_id=winner.guest_id if winner else None,
            winner_name=winner.nickname if winner else None,
            players=players_data,
            used_words=used_words_data,
            total_rounds=game_state.get('round_number', 1),
            game_duration=f"{len(word_entries)}턴 완료",
            total_words=len(word_entries),
            average_response_time=round(game_stats.get('average_response_time', 0.0), 1),
            longest_word=game_stats.get('longest_word', ''),
            fastest_response=round(game_stats.get('fastest_response', 0.0), 1),
            slowest_response=round(game_stats.get('slowest_response', 0.0), 1),
            mvp_id=winner.guest_id if winner else None,
            mvp_name=winner.nickname if winner else "없음",
            started_at=datetime.fromisoformat(game_state['created_at']) if game_state.get('created_at') else datetime.now(),
            ended_at=datetime.now()
        )
    
    async def _get_fallback_game_result(self, room_id: int, room):
        """데모 데이터 또는 오류 응답을 생성합니다."""
        from schemas.gameroom_schema import GameResultResponse, PlayerGameResult, WordChainEntry
        
        if room.status in [GameStatus.FINISHED.value, 'FINISHED']:
            # 완료된 게임이지만 데이터가 없는 경우 - 데모 데이터 제공
            return self._create_demo_game_result(room_id, room)
        else:
            # 게임이 진행 중이거나 시작되지 않은 경우
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임 결과 데이터를 찾을 수 없습니다. 게임이 아직 시작되지 않았거나 진행 중입니다."
            )
    
    def _create_demo_game_result(self, room_id: int, room):
        """데모 게임 결과를 생성합니다."""
        from schemas.gameroom_schema import GameResultResponse, PlayerGameResult, WordChainEntry
        
        participants = self.repository.find_room_participants(room_id)
        
        # 참가자 데이터로 기본 결과 생성
        players_data = []
        for idx, p in enumerate(participants):
            if p.left_at is None:  # 나가지 않은 참가자만
                players_data.append(PlayerGameResult(
                    guest_id=p.guest.guest_id,
                    nickname=p.guest.nickname,
                    words_submitted=5 + idx,
                    total_score=(5 + idx) * 50,
                    avg_response_time=8.5 - idx * 0.5,
                    longest_word="끝말잇기" if idx == 0 else "기차",
                    rank=idx + 1
                ))
        
        # 데모 단어 데이터
        demo_words = ["끝말잇기", "기차", "차례", "례회", "회사", "사과", "과일", "일기", "기록", "록음"]
        used_words_data = []
        for idx, word in enumerate(demo_words):
            player_idx = idx % len(players_data)
            if player_idx < len(players_data):
                used_words_data.append(WordChainEntry(
                    word=word,
                    player_id=players_data[player_idx].guest_id,
                    player_name=players_data[player_idx].nickname,
                    timestamp=datetime.now() - timedelta(minutes=10-idx),
                    response_time=7.5 + (idx % 3)
                ))
        
        winner = players_data[0] if players_data else None
        
        return GameResultResponse(
            room_id=room_id,
            winner_id=winner.guest_id if winner else None,
            winner_name=winner.nickname if winner else None,
            players=players_data,
            used_words=used_words_data,
            total_rounds=2,
            game_duration="10분",
            total_words=len(demo_words),
            average_response_time=8.2,
            longest_word="끝말잇기",
            fastest_response=5.3,
            slowest_response=12.1,
            mvp_id=winner.guest_id if winner else None,
            mvp_name=winner.nickname if winner else "없음",
            started_at=room.started_at or datetime.now() - timedelta(minutes=10),
            ended_at=datetime.now()
        )
