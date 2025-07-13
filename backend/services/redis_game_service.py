"""
Redis 기반 실시간 게임 상태 관리 서비스
"""

import json
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from app_config import settings
import logging

logger = logging.getLogger(__name__)


class RedisGameService:
    """Redis 기반 게임 상태 관리"""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')  # Docker 환경 기본값 수정
        self.redis_client = None
        self.turn_timers = {}  # room_id별 타이머 태스크 저장
        print(f"[DEBUG] RedisGameService 초기화 - Redis URL: {self.redis_url}")
        
    async def connect(self):
        """Redis 연결"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise
    
    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis_client:
            await self.redis_client.close()
    
    # === 게임 상태 관리 ===
    
    async def create_game(self, room_id: int, participants: List[Dict], settings: Dict = None) -> bool:
        """새 게임 생성"""
        try:
            default_settings = {
                'turn_time_limit': 30,  # 30초 제한
                'max_rounds': 10,
                'word_min_length': 2,
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
            
            # 참가자별 개인 정보 저장
            for participant in participants:
                player_data = {
                    'guest_id': participant['guest_id'],
                    'nickname': participant['nickname'],
                    'score': 0,
                    'words_submitted': 0,
                    'items_used': [],
                    'status': 'active'
                }
                await self.redis_client.setex(
                    f"game:{room_id}:player:{participant['guest_id']}",
                    86400,
                    json.dumps(player_data)
                )
            
            logger.info(f"게임 생성: room_id={room_id}, participants={len(participants)}")
            return True
            
        except Exception as e:
            logger.error(f"게임 생성 실패: {e}")
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
            
            # 첫 번째 플레이어 알림 WebSocket 브로드캐스트
            current_player_nickname = game_state.get('first_player_nickname', '알 수 없음')
            try:
                from services.gameroom_service import ws_manager
                await ws_manager.broadcast_to_room(room_id, {
                    'type': 'game_started_redis',
                    'room_id': room_id,
                    'first_word': first_word,
                    'first_player_id': game_state['current_player_id'],
                    'first_player_nickname': current_player_nickname,
                    'message': f'🎮 게임이 시작되었습니다! 첫 번째 차례: {current_player_nickname}님',
                    'participants_order': [p['nickname'] for p in game_state['participants']],
                    'time_left': game_state['time_left']
                })
            except Exception as e:
                logger.error(f"게임 시작 알림 브로드캐스트 실패: {e}")
            
            logger.info(f"게임 시작: room_id={room_id}, first_word={first_word}, first_player={current_player_nickname}")
            return True
            
        except Exception as e:
            logger.error(f"게임 시작 실패: {e}")
            return False
    
    async def submit_word(self, room_id: int, guest_id: int, word: str) -> Dict[str, Any]:
        """단어 제출"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return {'success': False, 'message': '게임을 찾을 수 없습니다.'}
            
            if game_state['status'] != 'playing':
                return {'success': False, 'message': '게임이 진행 중이 아닙니다.'}
            
            if game_state['current_player_id'] != guest_id:
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
                return {'success': False, 'message': validation_result['message']}
            
            # 현재 플레이어 정보 가져오기
            current_player = None
            for participant in game_state.get('participants', []):
                if participant['guest_id'] == guest_id:
                    current_player = participant
                    break
            
            # 단어별 상세 정보 저장
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
            
            # Redis에 단어별 상세 정보 저장
            await self._save_word_entry(room_id, word_entry)
            
            # 단어 추가
            game_state['used_words'].append(word)
            game_state['last_word'] = word
            game_state['last_character'] = word[-1]
            
            # 플레이어 정보 업데이트 (응답 시간 포함)
            await self._update_player_stats(room_id, guest_id, word, response_time)
            
            # 다음 턴으로 이동
            await self._advance_turn(room_id, game_state)
            
            # 게임 종료 조건 확인
            game_over_check = await self._check_game_over(game_state)
            
            result = {
                'success': True,
                'word': word,
                'last_character': word[-1],
                'next_player_id': game_state['current_player_id'],
                'current_round': game_state['round_number'],
                'max_rounds': game_state['game_settings']['max_rounds'],
                'game_over': game_over_check['game_over'],
                'game_over_reason': game_over_check.get('reason', ''),
                'time_left': game_state['time_left']
            }
            
            if game_over_check['game_over']:
                game_state['status'] = 'finished'
                await self._save_game_state(room_id, game_state)
                await self.stop_turn_timer(room_id)
            else:
                await self.start_turn_timer(room_id)
            
            return result
            
        except Exception as e:
            logger.error(f"단어 제출 실패: {e}")
            return {'success': False, 'message': '단어 제출 중 오류가 발생했습니다.'}
    
    async def _validate_word(self, game_state: Dict, word: str) -> Dict[str, Any]:
        """단어 유효성 검증"""
        word = word.strip()
        
        # 길이 검증
        min_length = game_state['game_settings']['word_min_length']
        if len(word) < min_length:
            return {'valid': False, 'message': f'단어는 최소 {min_length}글자 이상이어야 합니다.'}
        
        # 한글 검증
        if not all(ord('가') <= ord(char) <= ord('힣') for char in word):
            return {'valid': False, 'message': '한글만 입력 가능합니다.'}
        
        # 시작 글자 검증
        if game_state['last_character'] and word[0] != game_state['last_character']:
            return {'valid': False, 'message': f"'{game_state['last_character']}'로 시작하는 단어를 입력하세요."}
        
        # 중복 단어 검증
        if word in game_state['used_words']:
            return {'valid': False, 'message': '이미 사용된 단어입니다.'}
        
        # TODO: 사전 검증 (외부 API 호출)
        # if not await self._check_dictionary(word):
        #     return {'valid': False, 'message': '사전에 없는 단어입니다.'}
        
        return {'valid': True}
    
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
                
                await self.redis_client.setex(player_key, 86400, json.dumps(player_data))
                
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
        
        # TODO: 다른 종료 조건들
        # - 모든 플레이어가 나갔을 때
        # - 시간 초과
        # - 특별한 이벤트
        
        return {'game_over': False}
    
    # === 타이머 관리 ===
    
    async def start_turn_timer(self, room_id: int):
        """턴 타이머 시작"""
        # 기존 타이머 정지
        await self.stop_turn_timer(room_id)
        
        # 새 타이머 시작
        timer_task = asyncio.create_task(self._run_turn_timer(room_id))
        self.turn_timers[room_id] = timer_task
    
    async def stop_turn_timer(self, room_id: int):
        """턴 타이머 정지"""
        if room_id in self.turn_timers:
            self.turn_timers[room_id].cancel()
            del self.turn_timers[room_id]
    
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
                
                # WebSocket으로 시간 업데이트 브로드캐스트
                await self._broadcast_time_update(room_id, remaining)
            
            # 시간 초과 처리
            await self._handle_time_over(room_id)
            
        except asyncio.CancelledError:
            logger.info(f"타이머 취소됨: room_id={room_id}")
        except Exception as e:
            logger.error(f"타이머 오류: {e}")
    
    async def _broadcast_time_update(self, room_id: int, time_left: int):
        """시간 업데이트 브로드캐스트"""
        # 매초 브로드캐스트 (클라이언트 동기화를 위해)
        try:
            from services.gameroom_service import ws_manager
            await ws_manager.broadcast_to_room(room_id, {
                'type': 'game_time_update',
                'time_left': time_left,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"시간 업데이트 브로드캐스트 실패: {e}")
    
    async def _handle_time_over(self, room_id: int):
        """시간 초과 처리"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return
            
            # 현재 플레이어 패널티 또는 자동 턴 넘김
            await self._advance_turn(room_id, game_state)
            
            # 시간 초과 알림
            from services.gameroom_service import ws_manager
            await ws_manager.broadcast_to_room(room_id, {
                'type': 'game_time_over',
                'current_player_id': game_state['current_player_id'],
                'message': '시간 초과! 다음 플레이어 차례입니다.',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # 다음 턴 타이머 시작
            await self.start_turn_timer(room_id)
            
        except Exception as e:
            logger.error(f"시간 초과 처리 실패: {e}")
    
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
            
            logger.info(f"게임 종료: room_id={room_id}")
            return True
            
        except Exception as e:
            logger.error(f"게임 종료 실패: {e}")
            return False
    
    async def cleanup_game(self, room_id: int):
        """게임 데이터 정리"""
        try:
            # 타이머 정지
            await self.stop_turn_timer(room_id)
            
            # Redis 키 삭제
            pattern = f"game:{room_id}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
            
            logger.info(f"게임 데이터 정리 완료: room_id={room_id}")
            
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