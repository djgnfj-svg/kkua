"""
게임 상태 관리 서비스
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class GameStateManager:
    """게임 상태 생성 및 관리"""
    
    @staticmethod
    def create_initial_game_state(room_id: int, participants: List[Dict]) -> Dict[str, Any]:
        """초기 게임 상태 생성"""
        # 참가자 순서 랜덤화
        shuffled_participants = participants.copy()
        import random
        random.shuffle(shuffled_participants)
        
        # 첫 번째 플레이어 선택
        first_player = shuffled_participants[0]
        
        game_state = {
            'room_id': room_id,
            'status': 'waiting',
            'participants': shuffled_participants,
            'current_player_index': 0,
            'current_player': first_player,
            'used_words': [],
            'word_chain': [],
            'turn_count': 0,
            'time_left': 30,
            'last_word': '',
            'last_char': '',
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'ended_at': None
        }
        
        logger.info(f"초기 게임 상태 생성: room_id={room_id}, 참가자 수={len(participants)}")
        return game_state
    
    @staticmethod
    def start_game(game_state: Dict, first_word: str = "끝말잇기") -> Dict[str, Any]:
        """게임 시작"""
        game_state.update({
            'status': 'playing',
            'started_at': datetime.utcnow().isoformat(),
            'last_word': first_word,
            'last_char': first_word[-1] if first_word else '',
            'used_words': [first_word] if first_word else [],
            'time_left': 30
        })
        
        logger.info(f"게임 시작: room_id={game_state['room_id']}, 첫 단어='{first_word}'")
        return game_state
    
    @staticmethod
    def get_current_player(game_state: Dict) -> Dict:
        """현재 턴 플레이어 조회"""
        participants = game_state.get('participants', [])
        current_index = game_state.get('current_player_index', 0)
        
        if participants and 0 <= current_index < len(participants):
            return participants[current_index]
        return {}
    
    @staticmethod
    def move_to_next_player(game_state: Dict) -> Dict:
        """다음 플레이어로 턴 이동"""
        participants = game_state.get('participants', [])
        if not participants:
            return game_state
        
        current_index = game_state.get('current_player_index', 0)
        next_index = (current_index + 1) % len(participants)
        
        game_state.update({
            'current_player_index': next_index,
            'current_player': participants[next_index],
            'turn_count': game_state.get('turn_count', 0) + 1,
            'time_left': 30  # 새 턴 시작 시 시간 리셋
        })
        
        logger.debug(f"다음 플레이어로 이동: room_id={game_state['room_id']}, player={participants[next_index]['nickname']}")
        return game_state
    
    @staticmethod
    def add_word_to_chain(game_state: Dict, word: str, player_id: int) -> Dict:
        """단어 체인에 단어 추가"""
        word_entry = {
            'word': word,
            'player_id': player_id,
            'timestamp': datetime.utcnow().isoformat(),
            'turn': game_state.get('turn_count', 0)
        }
        
        # 사용된 단어 목록에 추가
        used_words = game_state.get('used_words', [])
        used_words.append(word)
        
        # 단어 체인에 추가
        word_chain = game_state.get('word_chain', [])
        word_chain.append(word_entry)
        
        game_state.update({
            'used_words': used_words,
            'word_chain': word_chain,
            'last_word': word,
            'last_char': word[-1] if word else ''
        })
        
        logger.info(f"단어 추가: room_id={game_state['room_id']}, word='{word}', player_id={player_id}")
        return game_state
    
    @staticmethod
    def end_game(game_state: Dict, reason: str = "completed") -> Dict:
        """게임 종료"""
        game_state.update({
            'status': 'finished',
            'ended_at': datetime.utcnow().isoformat(),
            'end_reason': reason
        })
        
        logger.info(f"게임 종료: room_id={game_state['room_id']}, reason='{reason}'")
        return game_state
    
    @staticmethod
    def is_word_valid(game_state: Dict, word: str) -> tuple[bool, str]:
        """단어 유효성 검증"""
        if not word or len(word) < 2:
            return False, "단어는 2글자 이상이어야 합니다"
        
        # 중복 사용 검증
        used_words = game_state.get('used_words', [])
        if word in used_words:
            return False, "이미 사용된 단어입니다"
        
        # 끝말잇기 규칙 검증
        last_word = game_state.get('last_word', '')
        if last_word and word[0] != game_state.get('last_char', ''):
            return False, f"'{game_state.get('last_char', '')}'(으)로 시작하는 단어여야 합니다"
        
        # 한글 검증 (간단한 검증)
        if not all('가' <= char <= '힣' for char in word):
            return False, "한글 단어만 입력 가능합니다"
        
        return True, "유효한 단어입니다"
    
    @staticmethod
    def calculate_game_statistics(game_state: Dict) -> Dict[str, Any]:
        """게임 통계 계산"""
        word_chain = game_state.get('word_chain', [])
        participants = game_state.get('participants', [])
        
        stats = {
            'total_words': len(word_chain),
            'total_turns': game_state.get('turn_count', 0),
            'duration_seconds': 0,
            'players': []
        }
        
        # 게임 지속시간 계산
        started_at = game_state.get('started_at')
        ended_at = game_state.get('ended_at')
        if started_at and ended_at:
            try:
                start_time = datetime.fromisoformat(started_at)
                end_time = datetime.fromisoformat(ended_at)
                stats['duration_seconds'] = int((end_time - start_time).total_seconds())
            except ValueError:
                logger.warning("시간 계산 실패")
        
        # 플레이어별 통계
        for participant in participants:
            player_id = participant.get('guest_id')
            player_words = [entry for entry in word_chain if entry.get('player_id') == player_id]
            
            player_stats = {
                'guest_id': player_id,
                'nickname': participant.get('nickname'),
                'words_count': len(player_words),
                'score': len(player_words) * 10,  # 단어당 10점
                'words': [entry['word'] for entry in player_words]
            }
            stats['players'].append(player_stats)
        
        logger.debug(f"게임 통계 계산 완료: room_id={game_state['room_id']}")
        return stats