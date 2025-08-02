"""
Redis 기반 실시간 게임 상태 관리 서비스
"""

import json
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import (
    RedisError, ConnectionError, TimeoutError, 
    ResponseError, BusyLoadingError, ReadOnlyError
)
from app_config import settings
from config.sentry_config import capture_redis_error, capture_game_event
import logging

logger = logging.getLogger(__name__)


class RedisGameService:
    """Redis 기반 게임 상태 관리"""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')  # Docker 환경 기본값 수정
        self.redis_client = None
        self.turn_timers = {}  # room_id별 타이머 태스크 저장
        self.background_tasks = set()  # 메모리 누수 방지를 위한 백그라운드 태스크 추적
        
        # 성능 최적화를 위한 Set 기반 추적
        self.ACTIVE_GAMES_SET = "active_games"  # 활성 게임 ID 추적용 Set
        self.PLAYER_GAMES_PREFIX = "player_games:"  # 플레이어별 참여 게임 추적
        
        # WebSocket 트래픽 최적화를 위한 메시지 중복 제거
        self.last_broadcast_data = {}  # room_id별 마지막 브로드캐스트 데이터 캐시
        
        logger.debug(f"RedisGameService 초기화 - Redis URL: {self.redis_url}")
        
    async def connect(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Redis 연결 (재시도 로직 포함)"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True,
                    socket_connect_timeout=5,  # 연결 타임아웃
                    socket_timeout=5,  # 소켓 타임아웃
                    retry_on_timeout=True,
                    health_check_interval=30  # 연결 상태 체크 간격
                )
                await self.redis_client.ping()
                logger.info(f"Redis 연결 성공 (시도 {attempt + 1}/{max_retries})")
                return
            except redis.ConnectionError as e:
                last_exception = e
                logger.warning(f"Redis 연결 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"{retry_delay}초 후 재시도...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
            except redis.TimeoutError as e:
                last_exception = e
                logger.warning(f"Redis 연결 타임아웃 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
            except Exception as e:
                last_exception = e
                logger.error(f"예상치 못한 Redis 연결 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
        
        # 모든 재시도 실패
        logger.error(f"Redis 연결 완전 실패 (URL: {self.redis_url})")
        raise ConnectionError(f"Redis 서버에 연결할 수 없습니다: {last_exception}")
    
    async def disconnect(self):
        """Redis 연결 해제 및 완전한 리소스 정리"""
        # 모든 타이머 정리
        await self.cleanup_all_timers()
        
        # 모든 백그라운드 태스크 정리
        await self.cleanup_background_tasks()
        
        # Redis 연결 해제
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis 연결 해제 완료")
            except Exception as e:
                logger.error(f"Redis 연결 해제 중 오류: {e}")
    
    async def cleanup_all_timers(self):
        """모든 활성 타이머 정리 (메모리 누수 방지)"""
        timer_rooms = list(self.turn_timers.keys())
        for room_id in timer_rooms:
            await self.stop_turn_timer(room_id)
        logger.info(f"모든 타이머 정리 완료: {len(timer_rooms)}개")
    
    async def cleanup_background_tasks(self):
        """모든 백그라운드 태스크 정리 (메모리 누수 방지)"""
        if self.background_tasks:
            # 모든 태스크 취소
            for task in list(self.background_tasks):
                if not task.done():
                    task.cancel()
            
            # 모든 취소된 태스크가 완료될 때까지 기다림
            if self.background_tasks:
                try:
                    await asyncio.gather(*self.background_tasks, return_exceptions=True)
                except Exception as e:
                    logger.warning(f"백그라운드 태스크 정리 중 오류: {e}")
            
            self.background_tasks.clear()
            logger.info("모든 백그라운드 태스크 정리 완료")
    
    def create_background_task(self, coro, name: str = None):
        """메모리 누수 방지를 위한 안전한 백그라운드 태스크 생성"""
        task = asyncio.create_task(coro, name=name)
        self.background_tasks.add(task)
        task.add_done_callback(lambda t: self.background_tasks.discard(t))
        return task
    
    async def _smart_broadcast(self, room_id: int, message: dict, message_key: str = None):
        """중복 방지 스마트 브로드캐스트 (WebSocket 트래픽 최적화)"""
        try:
            # 메시지 키가 없으면 타입을 기반으로 생성
            if message_key is None:
                message_key = message.get('type', 'unknown')
            
            cache_key = f"{room_id}:{message_key}"
            
            # 중복 메시지 확인 (타이머 메시지 제외)
            if message_key != 'game_time_update' and message_key.startswith('game_time'):
                # 타이머 메시지는 항상 전송 (실시간성 중요)
                pass
            else:
                # 다른 메시지는 중복 검사
                last_message = self.last_broadcast_data.get(cache_key)
                if last_message and self._messages_equal(last_message, message):
                    logger.debug(f"중복 메시지 생략: room_id={room_id}, type={message_key}")
                    return
            
            # 브로드캐스트 실행
            from services.gameroom_service import ws_manager
            await ws_manager.broadcast_to_room(room_id, message)
            
            # 캐시 업데이트 (메모리 절약을 위해 최대 100개 방까지만)
            if len(self.last_broadcast_data) < 100:
                self.last_broadcast_data[cache_key] = message.copy()
            
            logger.debug(f"스마트 브로드캐스트 성공: room_id={room_id}, type={message_key}")
            
        except Exception as e:
            logger.error(f"스마트 브로드캐스트 실패: {e}")
    
    def _messages_equal(self, msg1: dict, msg2: dict) -> bool:
        """메시지 동등성 검사 (중요 필드만 비교)"""
        # 타임스탬프 제외하고 비교
        ignore_keys = {'timestamp', 'updated_at'}
        
        filtered_msg1 = {k: v for k, v in msg1.items() if k not in ignore_keys}
        filtered_msg2 = {k: v for k, v in msg2.items() if k not in ignore_keys}
        
        return filtered_msg1 == filtered_msg2
    
    async def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection check failed: {e}")
            capture_redis_error(e, operation="connection_check")
            return False
        except (ResponseError, BusyLoadingError) as e:
            logger.warning(f"Redis server error during ping: {e}")
            capture_redis_error(e, operation="ping")
            return False
        except RedisError as e:
            logger.error(f"Redis error during connection check: {e}")
            capture_redis_error(e, operation="connection_check")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Redis connection check: {e}", exc_info=True)
            return False
    
    async def ensure_connection(self):
        """연결 상태 확인 후 필요시 재연결"""
        if not await self.is_connected():
            logger.warning("Redis 연결이 끊어짐, 재연결 시도")
            await self.connect()
    
    # === 게임 상태 관리 ===
    
    async def create_game(self, room_id: int, participants: List[Dict], settings: Dict = None, game_mode: Dict = None) -> bool:
        """새 게임 생성 (게임 모드 지원)"""
        try:
            # 기존 게임 데이터가 있다면 정리
            await self.cleanup_game(room_id)
            
            # 게임 모드 기반 기본 설정
            if game_mode:
                default_settings = {
                    'turn_time_limit': game_mode.get('turn_time_limit', 30),
                    'max_rounds': game_mode.get('max_rounds', 10),
                    'word_min_length': game_mode.get('min_word_length', 2),
                    'word_max_length': game_mode.get('max_word_length', 10),
                    'score_multiplier': game_mode.get('score_multiplier', 1.0),
                    'enable_advanced_scoring': game_mode.get('enable_advanced_scoring', True),
                    'special_rules': game_mode.get('special_rules', {}),
                    'mode_name': game_mode.get('name', 'classic'),
                    'mode_display_name': game_mode.get('display_name', '클래식 모드'),
                    'use_items': True
                }
            else:
                # 클래식 모드 기본 설정
                default_settings = {
                    'turn_time_limit': 30,
                    'max_rounds': 10,
                    'word_min_length': 2,
                    'word_max_length': 10,
                    'score_multiplier': 1.0,
                    'enable_advanced_scoring': True,
                    'special_rules': {},
                    'mode_name': 'classic',
                    'mode_display_name': '클래식 모드',
                    'use_items': True
                }
            
            if settings:
                default_settings.update(settings)
            
            # 참가자 순서 무작위 섞기 (게임의 공정성과 재미를 위해)
            shuffled_participants = participants.copy()
            random.shuffle(shuffled_participants)
            
            # 첫 번째 플레이어도 무작위 선택
            first_player_index = random.randint(0, len(shuffled_participants) - 1) if shuffled_participants else 0
            
            game_state = {
                'room_id': room_id,
                'status': 'waiting',  # waiting, playing, paused, finished
                'participants': shuffled_participants,  # 섞인 순서로 저장
                'current_turn_index': first_player_index,
                'current_player_id': shuffled_participants[first_player_index]['guest_id'] if shuffled_participants else None,
                'first_player_nickname': shuffled_participants[first_player_index]['nickname'] if shuffled_participants else None,
                'round_number': 1,
                'used_words': [],
                'last_word': '',
                'last_character': '',
                'turn_start_time': None,
                'time_left': default_settings['turn_time_limit'],
                'game_settings': default_settings,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Redis에 게임 상태 저장 (24시간 만료)
            await self.redis_client.setex(
                f"game:{room_id}", 
                86400,  # 24시간
                json.dumps(game_state)
            )
            
            # 활성 게임 목록에 추가
            await self.redis_client.sadd(self.ACTIVE_GAMES_SET, room_id)
            await self.redis_client.expire(self.ACTIVE_GAMES_SET, 86400)
            
            # 참가자별 개인 정보 저장 및 플레이어 게임 추적
            for participant in participants:
                guest_id = participant['guest_id']
                player_data = {
                    'guest_id': guest_id,
                    'nickname': participant['nickname'],
                    'score': 0,
                    'words_submitted': 0,
                    'items_used': [],
                    'status': 'active'
                }
                await self.redis_client.setex(
                    f"game:{room_id}:player:{guest_id}",
                    86400,
                    json.dumps(player_data)
                )
                
                # 플레이어별 참여 게임 추적 (Set 사용)
                player_games_key = f"{self.PLAYER_GAMES_PREFIX}{guest_id}"
                await self.redis_client.sadd(player_games_key, room_id)
                await self.redis_client.expire(player_games_key, 86400)
            
            logger.info(f"게임 생성: room_id={room_id}, participants={len(participants)}")
            # Sentry 게임 이벤트 캡처
            capture_game_event("game_created", {
                "room_id": room_id,
                "participant_count": len(participants),
                "game_settings": default_settings
            })
            return True
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis 연결 오류로 게임 생성 실패: room_id={room_id}, error={e}")
            capture_redis_error(e, operation="game_creation", key=f"game:{room_id}")
            return False
        except (ResponseError, RedisError) as e:
            logger.error(f"Redis 서버 오류로 게임 생성 실패: room_id={room_id}, error={e}")
            capture_redis_error(e, operation="game_creation", key=f"game:{room_id}")
            return False
        except (ValueError, KeyError) as e:
            logger.error(f"잘못된 데이터로 게임 생성 실패: room_id={room_id}, error={e}")
            return False
        except Exception as e:
            logger.error(f"예상치 못한 게임 생성 실패: room_id={room_id}, error={e}", exc_info=True)
            return False
    
    async def start_game(self, room_id: int, first_word: str = "끝말잇기") -> bool:
        """게임 시작"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return False
            
            game_state['status'] = 'playing'
            game_state['last_word'] = first_word
            game_state['last_character'] = first_word[-1]
            game_state['turn_start_time'] = datetime.utcnow().isoformat()
            game_state['time_left'] = game_state['game_settings']['turn_time_limit']
            game_state['used_words'] = [first_word]
            game_state['updated_at'] = datetime.utcnow().isoformat()
            
            await self._save_game_state(room_id, game_state)
            
            # 턴 타이머 시작
            await self.start_turn_timer(room_id)
            
            # 첫 번째 플레이어 알림 WebSocket 브로드캐스트 (스마트 브로드캐스트 사용)
            current_player_nickname = game_state.get('first_player_nickname', '알 수 없음')
            try:
                await self._smart_broadcast(room_id, {
                    'type': 'game_started_redis',
                    'room_id': room_id,
                    'first_word': first_word,
                    'first_player_id': game_state['current_player_id'],
                    'first_player_nickname': current_player_nickname,
                    'message': f'🎮 게임이 시작되었습니다! 첫 번째 차례: {current_player_nickname}님',
                    'participants_order': [p['nickname'] for p in game_state['participants']],
                    'time_left': game_state['time_left']
                }, 'game_started_redis')
            except Exception as e:
                logger.error(f"게임 시작 알림 브로드캐스트 실패: {e}")
            
            logger.info(f"게임 시작: room_id={room_id}, first_word={first_word}, first_player={current_player_nickname}")
            return True
            
        except Exception as e:
            logger.error(f"게임 시작 실패: {e}")
            return False
    
    async def submit_word(self, room_id: int, guest_id: int, word: str) -> Dict[str, Any]:
        """단어 제출 (Race Condition 방지를 위한 Redis 트랜잭션 사용)"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Redis 트랜잭션을 위한 키 감시 시작
                game_key = f"game:{room_id}"
                async with self.redis_client.pipeline(transaction=True) as pipe:
                    await pipe.watch(game_key)
                    
                    # 감시 중인 키의 현재 상태 조회
                    game_state_str = await self.redis_client.get(game_key)
                    if not game_state_str:
                        await pipe.unwatch()
                        return {'success': False, 'message': '게임을 찾을 수 없습니다.'}
                    
                    game_state = json.loads(game_state_str)
                    
                    # 기본 검증 (트랜잭션 외부에서 빠른 실패)
                    if game_state['status'] != 'playing':
                        await pipe.unwatch()
                        return {'success': False, 'message': '게임이 진행 중이 아닙니다.'}
                    
                    if game_state['current_player_id'] != guest_id:
                        await pipe.unwatch()
                        return {'success': False, 'message': '당신의 턴이 아닙니다.'}
                    
                    # 응답 시간 계산
                    turn_start_time = game_state.get('turn_start_time')
                    response_time = 0.0
                    if turn_start_time:
                        try:
                            start_dt = datetime.fromisoformat(turn_start_time)
                            response_time = (datetime.utcnow() - start_dt).total_seconds()
                        except Exception as e:
                            logger.warning(f"응답 시간 계산 실패: {e}")
                            response_time = 0.0
                    
                    # 단어 검증
                    validation_result = await self._validate_word(game_state, word)
                    if not validation_result['valid']:
                        await pipe.unwatch()
                        # 잘못된 단어 제출 시 연속 성공 초기화
                        await self._reset_consecutive_success(room_id, guest_id)
                        return {'success': False, 'message': validation_result['message']}
                    
                    # 현재 플레이어 정보 가져오기
                    current_player = None
                    for participant in game_state.get('participants', []):
                        if participant['guest_id'] == guest_id:
                            current_player = participant
                            break
                    
                    # 단어별 상세 정보 준비
                    word_entry = {
                        'word': word,
                        'player_id': guest_id,
                        'player_nickname': current_player['nickname'] if current_player else '알 수 없음',
                        'submitted_at': datetime.utcnow().isoformat(),
                        'response_time': round(response_time, 2),
                        'turn_number': len(game_state['used_words']) + 1,
                        'word_length': len(word),
                        'round_number': game_state.get('round_number', 1)
                    }
                    
                    # === 원자적 업데이트 시작 ===
                    pipe.multi()
                    
                    # 1. 게임 상태 업데이트
                    game_state['used_words'].append(word)
                    game_state['last_word'] = word
                    game_state['last_character'] = word[-1]
                    
                    # 2. 다음 턴으로 이동 (advance_turn 로직 인라인화)
                    participants = game_state['participants']
                    current_index = game_state.get('current_turn_index', 0)
                    
                    # 다음 플레이어 인덱스 계산
                    next_index = (current_index + 1) % len(participants)
                    game_state['current_turn_index'] = next_index
                    game_state['current_player_id'] = participants[next_index]['guest_id']
                    game_state['current_player_nickname'] = participants[next_index]['nickname']
                    
                    # 한 라운드 완료 시 라운드 증가
                    if next_index == 0:
                        game_state['round_number'] += 1
                    
                    # 턴 시간 초기화
                    game_state['turn_start_time'] = datetime.utcnow().isoformat()
                    game_state['time_left'] = game_state['game_settings']['turn_time_limit']
                    game_state['updated_at'] = datetime.utcnow().isoformat()
                    
                    # 3. 게임 종료 조건 확인
                    game_over_check = await self._check_game_over(game_state)
                    if game_over_check['game_over']:
                        game_state['status'] = 'finished'
                    
                    # 4. Redis에 업데이트된 게임 상태 저장
                    pipe.setex(game_key, 86400, json.dumps(game_state))
                    
                    # 5. 단어별 상세 정보 저장
                    word_key = f"game:{room_id}:words"
                    pipe.lpush(word_key, json.dumps(word_entry))
                    pipe.expire(word_key, 86400)
                    
                    # 6. 플레이어 통계 업데이트 (트랜잭션 내에서)
                    player_key = f"game:{room_id}:player:{guest_id}"
                    player_data_str = await self.redis_client.get(player_key)
                    
                    if player_data_str:
                        player_data = json.loads(player_data_str)
                    else:
                        # 플레이어 데이터가 없으면 기본 데이터로 초기화
                        logger.warning(f"플레이어 데이터가 없어 새로 생성: room_id={room_id}, guest_id={guest_id}")
                        player_data = {
                            'guest_id': guest_id,
                            'score': 0,
                            'words_submitted': 0,
                            'total_response_time': 0.0,
                            'fastest_response': float('inf'),
                            'slowest_response': 0.0,
                            'longest_word': '',
                            'created_at': datetime.utcnow().isoformat()
                        }
                    
                    # 고급 점수 계산 시스템 적용
                    from services.advanced_score_service import get_score_calculator
                    score_calculator = get_score_calculator()
                    
                    # 연속 성공 횟수 계산
                    consecutive_success = player_data.get('consecutive_success', 0) + 1
                    
                    # 고급 점수 계산 (게임 모드 배수 적용)
                    game_mode_multiplier = game_state['game_settings'].get('score_multiplier', 1.0)
                    special_rules = game_state['game_settings'].get('special_rules', {})
                    
                    score_info = score_calculator.calculate_word_score(
                        word=word,
                        response_time=response_time,
                        consecutive_success=consecutive_success,
                        game_context={
                            'room_id': room_id,
                            'game_mode_multiplier': game_mode_multiplier,
                            'special_rules': special_rules
                        }
                    )
                    
                    # 게임 모드 배수 적용
                    if game_mode_multiplier != 1.0:
                        score_info['final_score'] = int(score_info['final_score'] * game_mode_multiplier)
                        score_info['mode_multiplier'] = game_mode_multiplier
                        score_info['total_multiplier'] = score_info['total_multiplier'] * game_mode_multiplier
                    
                    # 통계 업데이트 (고급 점수 시스템 적용)
                    player_data['score'] += score_info['final_score']
                    player_data['words_submitted'] += 1
                    player_data['total_response_time'] += response_time
                    player_data['consecutive_success'] = consecutive_success
                    
                    # 점수 상세 정보 저장
                    if 'score_history' not in player_data:
                        player_data['score_history'] = []
                    player_data['score_history'].append({
                        'word': word,
                        'score_info': score_info,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    if response_time < player_data['fastest_response']:
                        player_data['fastest_response'] = response_time
                    if response_time > player_data['slowest_response']:
                        player_data['slowest_response'] = response_time
                    if len(word) > len(player_data['longest_word']):
                        player_data['longest_word'] = word
                    
                    player_data['updated_at'] = datetime.utcnow().isoformat()
                    
                    pipe.setex(player_key, 86400, json.dumps(player_data))
                    
                    # 트랜잭션 실행
                    await pipe.execute()
                    
                    # === 원자적 업데이트 완료 ===
                    
                    # 결과 준비 (고급 점수 정보 포함)
                    result = {
                        'success': True,
                        'word': word,
                        'last_character': word[-1],
                        'next_player_id': game_state['current_player_id'],
                        'current_round': game_state['round_number'],
                        'max_rounds': game_state['game_settings']['max_rounds'],
                        'game_over': game_over_check['game_over'],
                        'game_over_reason': game_over_check.get('reason', ''),
                        'time_left': game_state['time_left'],
                        'score_info': score_info,
                        'player_total_score': player_data['score']
                    }
                    
                    # 타이머 관리 (트랜잭션 외부)
                    if game_over_check['game_over']:
                        await self.stop_turn_timer(room_id)
                    else:
                        await self.start_turn_timer(room_id)
                    
                    logger.info(f"단어 제출 성공 (트랜잭션): room_id={room_id}, guest_id={guest_id}, word={word}")
                    return result
                    
            except Exception as e:
                error_message = str(e)
                if "WATCH" in error_message or "EXEC" in error_message or "concurrent" in error_message.lower():
                    # 동시성 충돌로 인한 재시도
                    retry_count += 1
                    logger.warning(f"동시성 충돌 감지 - 재시도 {retry_count}/{max_retries}: room_id={room_id}, guest_id={guest_id}")
                    if retry_count < max_retries:
                        # 짧은 지연 후 재시도
                        import asyncio
                        await asyncio.sleep(0.01 * retry_count)  # 10ms, 20ms, 30ms
                        continue
                    else:
                        logger.error(f"단어 제출 최대 재시도 초과: room_id={room_id}, guest_id={guest_id}")
                        return {'success': False, 'message': '동시 접근으로 인해 단어 제출에 실패했습니다. 다시 시도해주세요.'}
                else:
                    # 다른 종류의 오류
                    logger.error(f"단어 제출 실패: {e}")
                    return {'success': False, 'message': '단어 제출 중 오류가 발생했습니다.'}
        
        # 모든 재시도 실패
        return {'success': False, 'message': '동시 접근으로 인해 단어 제출에 실패했습니다. 다시 시도해주세요.'}
    
    async def _validate_word(self, game_state: Dict, word: str) -> Dict[str, Any]:
        """단어 유효성 검증"""
        word = word.strip()
        
        # 게임 모드 설정 가져오기
        game_settings = game_state['game_settings']
        
        # 길이 검증 (게임 모드별 설정 적용)
        min_length = game_settings.get('word_min_length', 2)
        max_length = game_settings.get('word_max_length', 10)
        
        if len(word) < min_length:
            return {'valid': False, 'message': f'단어는 최소 {min_length}글자 이상이어야 합니다.'}
        
        if len(word) > max_length:
            return {'valid': False, 'message': f'단어는 최대 {max_length}글자 이하여야 합니다.'}
        
        # 한글 검증
        if not all(ord('가') <= ord(char) <= ord('힣') for char in word):
            return {'valid': False, 'message': '한글만 입력 가능합니다.'}
        
        # 시작 글자 검증
        if game_state['last_character'] and word[0] != game_state['last_character']:
            return {'valid': False, 'message': f"'{game_state['last_character']}'로 시작하는 단어를 입력하세요."}
        
        # 중복 단어 검증
        if word in game_state['used_words']:
            return {'valid': False, 'message': '이미 사용된 단어입니다.'}
        
        # 특수 모드 규칙 적용
        special_rules = game_settings.get('special_rules', {})
        
        # 마라톤 모드: 긴 단어만 허용
        if special_rules.get('long_words_only') and len(word) < 5:
            return {'valid': False, 'message': '마라톤 모드에서는 5글자 이상 단어만 사용할 수 있습니다.'}
        
        # 기본 한국어 단어 검증 (간단한 패턴 체크)
        if not await self._validate_korean_word(word):
            return {'valid': False, 'message': '올바른 한국어 단어가 아닙니다.'}
        
        return {'valid': True}
    
    async def _validate_korean_word(self, word: str) -> bool:
        """한국어 단어 기본 검증"""
        import re
        
        # 한글만 포함하는지 확인
        korean_pattern = re.compile(r'^[가-힣]+$')
        if not korean_pattern.match(word):
            return False
        
        # 단어 길이 제한 (2-10글자)
        if len(word) < 2 or len(word) > 10:
            return False
        
        # 금지 단어 목록 (기본적인 필터링)
        forbidden_words = {'바보', '멍청이', '시발', '개새끼'}
        if word in forbidden_words:
            return False
        
        return True
    
    async def _save_word_entry(self, room_id: int, word_entry: Dict):
        """단어별 상세 정보를 Redis에 저장"""
        try:
            # 단어별 상세 정보 리스트에 추가
            words_key = f"game:{room_id}:words"
            words_data_str = await self.redis_client.get(words_key)
            
            if words_data_str:
                words_data = json.loads(words_data_str)
            else:
                words_data = []
                
            words_data.append(word_entry)
            await self.redis_client.setex(words_key, 86400, json.dumps(words_data))
            
            # 게임 통계 업데이트
            await self._update_game_stats(room_id, word_entry)
            
        except Exception as e:
            logger.error(f"단어 정보 저장 실패: {e}")
    
    async def _update_game_stats(self, room_id: int, word_entry: Dict):
        """게임 전체 통계 업데이트"""
        try:
            stats_key = f"game:{room_id}:stats"
            stats_data_str = await self.redis_client.get(stats_key)
            
            if stats_data_str:
                stats_data = json.loads(stats_data_str)
            else:
                stats_data = {
                    'fastest_response': None,
                    'slowest_response': None,
                    'longest_word': '',
                    'shortest_word': '',
                    'total_response_time': 0.0,
                    'total_words': 0
                }
            
            response_time = word_entry['response_time']
            word = word_entry['word']
            
            # 최단/최장 응답시간 업데이트
            if response_time > 0:
                if stats_data['fastest_response'] is None or response_time < stats_data['fastest_response']:
                    stats_data['fastest_response'] = response_time
                if stats_data['slowest_response'] is None or response_time > stats_data['slowest_response']:
                    stats_data['slowest_response'] = response_time
                stats_data['total_response_time'] += response_time
            
            # 최장/최단 단어 업데이트
            if len(word) > len(stats_data['longest_word']):
                stats_data['longest_word'] = word
            if not stats_data['shortest_word'] or len(word) < len(stats_data['shortest_word']):
                stats_data['shortest_word'] = word
                
            stats_data['total_words'] += 1
            
            await self.redis_client.setex(stats_key, 86400, json.dumps(stats_data))
            
        except Exception as e:
            logger.error(f"게임 통계 업데이트 실패: {e}")

    async def _update_player_stats(self, room_id: int, guest_id: int, word: str, response_time: float = 0.0):
        """플레이어 통계 업데이트"""
        try:
            player_key = f"game:{room_id}:player:{guest_id}"
            player_data_str = await self.redis_client.get(player_key)
            
            if player_data_str:
                player_data = json.loads(player_data_str)
            else:
                # 플레이어 데이터가 없으면 기본 데이터로 초기화
                logger.warning(f"플레이어 데이터가 없어 새로 생성: room_id={room_id}, guest_id={guest_id}")
                
                # 게임 상태에서 플레이어 정보 찾기
                game_state = await self.get_game_state(room_id)
                player_nickname = "Unknown Player"
                if game_state:
                    for participant in game_state.get('participants', []):
                        if participant['guest_id'] == guest_id:
                            player_nickname = participant['nickname']
                            break
                
                player_data = {
                    'guest_id': guest_id,
                    'nickname': player_nickname,
                    'score': 0,
                    'words_submitted': 0,
                    'items_used': [],
                    'status': 'active'
                }
            
            # 점수 및 통계 업데이트
            player_data['score'] += len(word) * 10  # 글자당 10점
            player_data['words_submitted'] += 1
            
            # 응답 시간 통계 추가
            if response_time > 0:
                if 'total_response_time' not in player_data:
                    player_data['total_response_time'] = 0.0
                if 'fastest_response' not in player_data:
                    player_data['fastest_response'] = None
                if 'slowest_response' not in player_data:
                    player_data['slowest_response'] = None
                if 'longest_word' not in player_data:
                    player_data['longest_word'] = ''
                    
                player_data['total_response_time'] += response_time
                
                if player_data['fastest_response'] is None or response_time < player_data['fastest_response']:
                    player_data['fastest_response'] = response_time
                if player_data['slowest_response'] is None or response_time > player_data['slowest_response']:
                    player_data['slowest_response'] = response_time
                if len(word) > len(player_data['longest_word']):
                    player_data['longest_word'] = word
            
            # Redis에 저장
            await self.redis_client.setex(player_key, 86400, json.dumps(player_data))
            logger.debug(f"플레이어 통계 업데이트: guest_id={guest_id}, score={player_data['score']}, words={player_data['words_submitted']}")
                
        except Exception as e:
            logger.error(f"플레이어 통계 업데이트 실패: {e}")
    
    async def _advance_turn(self, room_id: int, game_state: Dict):
        """다음 턴으로 진행"""
        participants = game_state['participants']
        current_index = game_state['current_turn_index']
        
        # 다음 플레이어
        next_index = (current_index + 1) % len(participants)
        game_state['current_turn_index'] = next_index
        game_state['current_player_id'] = participants[next_index]['guest_id']
        
        # 한 라운드 완료 시 라운드 증가
        if next_index == 0:
            game_state['round_number'] += 1
        
        # 턴 시간 초기화
        game_state['turn_start_time'] = datetime.utcnow().isoformat()
        game_state['time_left'] = game_state['game_settings']['turn_time_limit']
        game_state['updated_at'] = datetime.utcnow().isoformat()
        
        await self._save_game_state(room_id, game_state)
    
    async def _check_game_over(self, game_state: Dict) -> Dict[str, Any]:
        """게임 종료 조건 확인"""
        max_rounds = game_state['game_settings']['max_rounds']
        current_round = game_state['round_number']
        
        if current_round > max_rounds:
            return {
                'game_over': True,
                'reason': 'max_rounds_reached',
                'message': f'최대 라운드({max_rounds}) 완료'
            }
        
        # 추가 종료 조건들
        
        # 1. 모든 플레이어가 나갔을 때 (활성 플레이어가 1명 이하)
        active_players = [p for p in game_state.get('participants', []) if p.get('is_active', True)]
        if len(active_players) <= 1:
            return {
                'game_over': True,
                'reason': 'insufficient_players',
                'message': '참가자가 부족하여 게임이 종료됩니다.'
            }
        
        # 2. 게임 시간 초과 (최대 30분)
        game_duration = datetime.now() - datetime.fromisoformat(game_state.get('started_at', datetime.now().isoformat()))
        max_game_duration = timedelta(minutes=30)
        if game_duration > max_game_duration:
            return {
                'game_over': True,
                'reason': 'time_limit',
                'message': '게임 시간이 초과되어 종료됩니다.'
            }
        
        # 3. 연속으로 턴을 넘긴 횟수가 많을 때 (게임 정체 방지)
        consecutive_skips = game_state.get('consecutive_skips', 0)
        if consecutive_skips >= len(active_players) * 2:  # 모든 플레이어가 2회씩 넘긴 경우
            return {
                'game_over': True,
                'reason': 'consecutive_skips',
                'message': '연속으로 턴을 넘겨서 게임이 종료됩니다.'
            }
        
        return {'game_over': False}
    
    # === 타이머 관리 ===
    
    async def start_turn_timer(self, room_id: int):
        """턴 타이머 시작 (메모리 누수 방지)"""
        # 기존 타이머 정지
        await self.stop_turn_timer(room_id)
        
        # 새 타이머 시작
        timer_task = asyncio.create_task(self._run_turn_timer(room_id))
        self.turn_timers[room_id] = timer_task
        self.background_tasks.add(timer_task)
        
        # 태스크 완료 시 자동 정리
        timer_task.add_done_callback(lambda t: self.background_tasks.discard(t))
    
    async def stop_turn_timer(self, room_id: int):
        """턴 타이머 정지 (완전한 정리)"""
        if room_id in self.turn_timers:
            timer_task = self.turn_timers[room_id]
            timer_task.cancel()
            self.background_tasks.discard(timer_task)
            del self.turn_timers[room_id]
            
            # 취소된 태스크가 완전히 정리될 때까지 기다림
            try:
                await timer_task
            except asyncio.CancelledError:
                pass  # 예상된 취소
            except Exception as e:
                logger.warning(f"타이머 태스크 정리 중 오류: {e}")
    
    async def _run_turn_timer(self, room_id: int):
        """턴 타이머 실행"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return
            
            time_limit = game_state['game_settings']['turn_time_limit']
            
            for remaining in range(time_limit, 0, -1):
                await asyncio.sleep(1)
                
                # 게임 상태 확인
                current_state = await self.get_game_state(room_id)
                if not current_state or current_state['status'] != 'playing':
                    return
                
                # 시간 업데이트
                current_state['time_left'] = remaining
                current_state['updated_at'] = datetime.utcnow().isoformat()
                await self._save_game_state(room_id, current_state)
                
                # 중요한 순간에만 WebSocket 브로드캐스트 (성능 최적화)
                await self._broadcast_time_update(room_id, remaining)
            
            # 시간 초과 처리
            await self._handle_time_over(room_id)
            
        except asyncio.CancelledError:
            logger.info(f"타이머 취소됨: room_id={room_id}")
        except Exception as e:
            logger.error(f"타이머 오류: {e}")
    
    async def _broadcast_time_update(self, room_id: int, time_left: int):
        """시간 업데이트 브로드캐스트 (고도로 최적화된 빈도)"""
        # 매우 효율적인 브로드캐스트 전략:
        # - 30초 이상: 30초, 60초에만 브로드캐스트
        # - 30-11초: 5초 간격 (30, 25, 20, 15)
        # - 10초 이하: 매초 브로드캐스트
        # - 5초 이하: 중요 알림 포함
        should_broadcast = (
            time_left <= 10 or  # 10초 이하는 매초 (중요)
            time_left in [15, 20, 25, 30] or  # 5초 간격의 중요 순간들
            (time_left >= 30 and time_left % 30 == 0)  # 30초 단위로만 (60초, 90초 등)
        )
        
        if should_broadcast:
            try:
                from services.gameroom_service import ws_manager
                
                # 메시지 타입 및 우선순위 결정
                if time_left <= 3:
                    message_type = 'game_time_urgent'
                    urgent_level = 'critical'
                elif time_left <= 5:
                    message_type = 'game_time_critical'
                    urgent_level = 'high'
                elif time_left <= 10:
                    message_type = 'game_time_warning'
                    urgent_level = 'medium'
                else:
                    message_type = 'game_time_update'
                    urgent_level = 'low'
                
                # 최적화된 메시지 구조 (불필요한 데이터 제거)
                message = {
                    'type': message_type,
                    'time_left': time_left,
                    'urgent_level': urgent_level
                }
                
                # 타임스탬프는 중요한 순간에만 포함 (데이터 절약)
                if time_left <= 10:
                    message['timestamp'] = datetime.utcnow().isoformat()
                
                await self._smart_broadcast(room_id, message, message_type)
                
            except Exception as e:
                logger.error(f"시간 업데이트 브로드캐스트 실패: {e}")
    
    async def _handle_time_over(self, room_id: int):
        """시간 초과 처리"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return
            
            # 현재 플레이어의 연속 성공 초기화 (시간 초과 패널티)
            current_player_id = game_state.get('current_player_id')
            if current_player_id:
                await self._reset_consecutive_success(room_id, current_player_id)
            
            # 현재 플레이어 패널티 또는 자동 턴 넘김
            await self._advance_turn(room_id, game_state)
            
            # 시간 초과 알림 (스마트 브로드캐스트 사용)
            await self._smart_broadcast(room_id, {
                'type': 'game_time_over',
                'current_player_id': game_state['current_player_id'],
                'message': '⏰ 시간 초과! 다음 플레이어 차례입니다.',
                'timestamp': datetime.utcnow().isoformat()
            }, 'game_time_over')
            
            # 다음 턴 타이머 시작
            await self.start_turn_timer(room_id)
            
        except Exception as e:
            logger.error(f"시간 초과 처리 실패: {e}")
    
    async def _reset_consecutive_success(self, room_id: int, guest_id: int):
        """플레이어의 연속 성공 횟수 초기화"""
        try:
            player_key = f"game:{room_id}:player:{guest_id}"
            player_data_str = await self.redis_client.get(player_key)
            
            if player_data_str:
                player_data = json.loads(player_data_str)
                player_data['consecutive_success'] = 0
                player_data['updated_at'] = datetime.utcnow().isoformat()
                await self.redis_client.setex(player_key, 86400, json.dumps(player_data))
                logger.debug(f"연속 성공 초기화: room_id={room_id}, guest_id={guest_id}")
        except Exception as e:
            logger.error(f"연속 성공 초기화 실패: {e}")
    
    # === 상태 조회 ===
    
    async def get_game_state(self, room_id: int) -> Optional[Dict]:
        """게임 상태 조회"""
        try:
            state_str = await self.redis_client.get(f"game:{room_id}")
            if state_str:
                return json.loads(state_str)
            return None
        except Exception as e:
            logger.error(f"게임 상태 조회 실패: {e}")
            return None
    
    async def get_player_stats(self, room_id: int, guest_id: int) -> Optional[Dict]:
        """플레이어 통계 조회"""
        try:
            # 게임 상태 먼저 확인
            game_state = await self.get_game_state(room_id)
            if not game_state:
                logger.warning(f"게임 상태 없음: room_id={room_id}")
                return None
            
            # 해당 플레이어가 이 게임의 참가자인지 확인
            is_participant = any(p['guest_id'] == guest_id for p in game_state.get('participants', []))
            if not is_participant:
                logger.warning(f"플레이어가 게임 참가자가 아님: room_id={room_id}, guest_id={guest_id}")
                return None
            
            stats_str = await self.redis_client.get(f"game:{room_id}:player:{guest_id}")
            if stats_str:
                return json.loads(stats_str)
            return None
        except Exception as e:
            logger.error(f"플레이어 통계 조회 실패: {e}")
            return None
    
    async def get_all_player_stats(self, room_id: int) -> List[Dict]:
        """모든 플레이어 통계 조회"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return []
            
            stats = []
            for participant in game_state['participants']:
                player_stats = await self.get_player_stats(room_id, participant['guest_id'])
                if player_stats:
                    # 평균 응답 시간 계산
                    if player_stats.get('words_submitted', 0) > 0 and player_stats.get('total_response_time', 0) > 0:
                        player_stats['average_response_time'] = round(
                            player_stats['total_response_time'] / player_stats['words_submitted'], 2
                        )
                    else:
                        player_stats['average_response_time'] = 0.0
                    stats.append(player_stats)
                else:
                    # 플레이어 통계가 없으면 기본 데이터로 생성
                    logger.warning(f"플레이어 통계 없음 - 기본 데이터 생성: room_id={room_id}, guest_id={participant['guest_id']}")
                    default_stats = {
                        'guest_id': participant['guest_id'],
                        'nickname': participant['nickname'],
                        'score': 0,
                        'words_submitted': 0,
                        'items_used': [],
                        'status': 'active',
                        'average_response_time': 0.0
                    }
                    stats.append(default_stats)
            
            return sorted(stats, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"전체 플레이어 통계 조회 실패: {e}")
            return []
    
    async def get_word_entries(self, room_id: int) -> List[Dict]:
        """단어별 상세 정보 조회"""
        try:
            words_key = f"game:{room_id}:words"
            words_data_str = await self.redis_client.get(words_key)
            
            if words_data_str:
                return json.loads(words_data_str)
            return []
            
        except Exception as e:
            logger.error(f"단어 정보 조회 실패: {e}")
            return []
    
    async def get_game_stats(self, room_id: int) -> Dict:
        """게임 전체 통계 조회"""
        try:
            stats_key = f"game:{room_id}:stats"
            stats_data_str = await self.redis_client.get(stats_key)
            
            if stats_data_str:
                stats_data = json.loads(stats_data_str)
                
                # 평균 응답 시간 계산
                if stats_data.get('total_words', 0) > 0 and stats_data.get('total_response_time', 0) > 0:
                    stats_data['average_response_time'] = round(
                        stats_data['total_response_time'] / stats_data['total_words'], 2
                    )
                else:
                    stats_data['average_response_time'] = 0.0
                    
                return stats_data
            return {}
            
        except Exception as e:
            logger.error(f"게임 통계 조회 실패: {e}")
            return {}
    
    async def get_final_game_results(self, room_id: int) -> Dict:
        """게임 종료 시 최종 결과 및 성과 정보 조회"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return {}
            
            # 모든 플레이어 통계 조회
            player_stats = await self.get_all_player_stats(room_id)
            game_stats = await self.get_game_stats(room_id)
            
            # 고급 점수 계산기를 사용해 성과 보너스 계산
            from services.advanced_score_service import get_score_calculator
            score_calculator = get_score_calculator()
            
            enhanced_player_stats = []
            for stats in player_stats:
                # 개별 성과 보너스 계산
                performance_bonus = score_calculator.calculate_game_performance_bonus(
                    stats, game_stats
                )
                
                enhanced_stats = {
                    **stats,
                    'performance_bonus': performance_bonus,
                    'final_score': stats['score'] + performance_bonus['total_bonus'],
                    'rank': 0  # 나중에 계산
                }
                enhanced_player_stats.append(enhanced_stats)
            
            # 최종 점수 기준으로 순위 매기기
            enhanced_player_stats.sort(key=lambda x: x['final_score'], reverse=True)
            for i, stats in enumerate(enhanced_player_stats):
                stats['rank'] = i + 1
            
            return {
                'game_state': game_state,
                'player_stats': enhanced_player_stats,
                'game_stats': game_stats,
                'word_entries': await self.get_word_entries(room_id)
            }
            
        except Exception as e:
            logger.error(f"최종 게임 결과 조회 실패: {e}")
            return {}
    
    async def _save_game_state(self, room_id: int, game_state: Dict):
        """게임 상태 저장"""
        try:
            await self.redis_client.setex(
                f"game:{room_id}",
                86400,  # 24시간
                json.dumps(game_state)
            )
        except Exception as e:
            logger.error(f"게임 상태 저장 실패: {e}")
    
    async def check_player_active_games(self, guest_id: int) -> List[int]:
        """플레이어가 참여 중인 활성 게임 목록 조회 (Set 기반 최적화)"""
        try:
            # Set에서 플레이어 참여 게임 목록 조회
            player_games_key = f"{self.PLAYER_GAMES_PREFIX}{guest_id}"
            game_ids = await self.redis_client.smembers(player_games_key)
            
            active_games = []
            for game_id_str in game_ids:
                try:
                    room_id = int(game_id_str)
                    # 게임이 실제로 활성 상태인지 확인
                    game_state = await self.get_game_state(room_id)
                    if game_state and game_state.get('status') in ['playing', 'waiting']:
                        active_games.append(room_id)
                    else:
                        # 비활성 게임은 Set에서 제거
                        await self.redis_client.srem(player_games_key, game_id_str)
                except (ValueError, TypeError):
                    # 잘못된 데이터는 Set에서 제거
                    await self.redis_client.srem(player_games_key, game_id_str)
            
            return active_games
        except Exception as e:
            logger.error(f"플레이어 활성 게임 조회 실패: {e}")
            return []
    
    async def validate_player_can_join(self, room_id: int, guest_id: int) -> tuple[bool, str]:
        """플레이어가 게임에 참여할 수 있는지 검증"""
        try:
            # 해당 플레이어의 다른 활성 게임 확인
            active_games = await self.check_player_active_games(guest_id)
            other_games = [game for game in active_games if game != room_id]
            
            if other_games:
                return False, f"다른 게임({other_games[0]})에 이미 참여 중입니다. 먼저 해당 게임을 종료해주세요."
            
            return True, "참여 가능"
        except Exception as e:
            logger.error(f"플레이어 참여 가능성 검증 실패: {e}")
            return True, "검증 실패하지만 허용"
    
    # === 게임 종료 ===
    
    async def end_game(self, room_id: int) -> bool:
        """게임 종료"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return False
            
            game_state['status'] = 'finished'
            game_state['ended_at'] = datetime.utcnow().isoformat()
            await self._save_game_state(room_id, game_state)
            
            # 타이머 정지
            await self.stop_turn_timer(room_id)
            
            # 활성 게임 목록에서 제거
            await self.redis_client.srem(self.ACTIVE_GAMES_SET, room_id)
            
            # 플레이어별 참여 게임 목록에서 제거
            for participant in game_state.get('participants', []):
                player_games_key = f"{self.PLAYER_GAMES_PREFIX}{participant['guest_id']}"
                await self.redis_client.srem(player_games_key, room_id)
            
            logger.info(f"게임 종료: room_id={room_id}")
            return True
            
        except Exception as e:
            logger.error(f"게임 종료 실패: {e}")
            return False
    
    async def cleanup_game(self, room_id: int):
        """게임 데이터 정리 (Set 기반 최적화)"""
        try:
            # 타이머 정지
            await self.stop_turn_timer(room_id)
            
            # 게임 상태를 먼저 조회해서 참가자 정보 확보
            game_state = await self.get_game_state(room_id)
            
            # 알려진 키들 직접 삭제 (keys() 명령어 사용 피함)
            keys_to_delete = [
                f"game:{room_id}",
                f"game:{room_id}:words",
                f"game:{room_id}:stats"
            ]
            
            # 플레이어별 키도 삭제 (게임 상태에서 참가자 정보 활용)
            if game_state and 'participants' in game_state:
                for participant in game_state['participants']:
                    guest_id = participant['guest_id']
                    keys_to_delete.append(f"game:{room_id}:player:{guest_id}")
                    
                    # 플레이어별 참여 게임 목록에서도 제거
                    player_games_key = f"{self.PLAYER_GAMES_PREFIX}{guest_id}"
                    await self.redis_client.srem(player_games_key, room_id)
            
            # 활성 게임 목록에서 제거
            await self.redis_client.srem(self.ACTIVE_GAMES_SET, room_id)
            
            # 키들 일괄 삭제
            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)
            
            logger.info(f"게임 데이터 정리 완료: room_id={room_id}, 삭제된 키 수: {len(keys_to_delete)}")
            
        except Exception as e:
            logger.error(f"게임 데이터 정리 실패: {e}")


# 싱글톤 인스턴스
_redis_game_service = None

async def get_redis_game_service() -> RedisGameService:
    """Redis 게임 서비스 싱글톤 인스턴스 반환"""
    global _redis_game_service
    if _redis_game_service is None:
        _redis_game_service = RedisGameService()
        await _redis_game_service.connect()
    return _redis_game_service