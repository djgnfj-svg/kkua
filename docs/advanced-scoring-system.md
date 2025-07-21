# 고급 점수 시스템 구현 가이드

## 📊 현재 점수 시스템 분석

### 기존 구현 (단순 점수 계산)
```python
# backend/services/redis_game_service.py:349
def calculate_score(self, word: str) -> int:
    return len(word) * 10  # 글자 수 × 10점
```

### 문제점
- **단조로운 점수 체계**: 글자 수만 고려
- **플레이어 기여도 미반영**: 빠른 응답, 연속 성공 등 무시
- **전략적 요소 부족**: 모든 단어가 동일한 가치
- **경쟁 요소 부족**: 상대적 성과 평가 없음

---

## 🎯 고급 점수 시스템 설계

### 점수 구성 요소
1. **기본 점수**: 글자 수 × 10 (기존 유지)
2. **속도 보너스**: 빠른 응답 시 추가 점수
3. **콤보 보너스**: 연속 성공 시 배수 증가
4. **희귀도 보너스**: 단어 사용 빈도에 따른 보너스
5. **난이도 보너스**: 받침 복잡도에 따른 보너스
6. **시간대 보너스**: 게임 후반부 가중치

### 점수 공식
```
총점 = (기본점수 + 속도보너스 + 특수보너스) × 콤보배수 × 희귀도배수 × 난이도배수
```

---

## 🔧 구현 계획

### Step 1: 데이터 모델 확장

#### 단어 통계 테이블 추가
```python
# backend/models/word_statistics_model.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class WordStatistics(Base):
    """단어 사용 통계 및 메타데이터"""
    __tablename__ = "word_statistics"
    
    word_id = Column(Integer, primary_key=True)
    word = Column(String(50), unique=True, nullable=False, index=True)
    usage_count = Column(Integer, default=0)  # 전체 사용 횟수
    first_used = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    
    # 난이도 관련 메타데이터
    syllable_count = Column(Integer)  # 음절 수
    consonant_complexity = Column(Float, default=1.0)  # 자음 복잡도 (1.0-3.0)
    vowel_complexity = Column(Float, default=1.0)     # 모음 복잡도 (1.0-3.0)
    ending_difficulty = Column(Float, default=1.0)    # 받침 난이도 (1.0-5.0)
    
    # 의미 관련 메타데이터
    category = Column(String(50))  # 단어 카테고리 (동물, 음식, 장소 등)
    rarity_score = Column(Float, default=1.0)  # 희귀도 점수 (1.0-5.0)
    definition = Column(Text)  # 단어 정의 (힌트용)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class PlayerScoreHistory(Base):
    """플레이어 점수 히스토리"""
    __tablename__ = "player_score_history"
    
    score_id = Column(Integer, primary_key=True)
    game_log_id = Column(Integer, ForeignKey("game_logs.id"))
    guest_id = Column(Integer, ForeignKey("guests.guest_id"))
    word = Column(String(50), nullable=False)
    
    # 점수 구성 요소
    base_score = Column(Integer, default=0)        # 기본 점수
    speed_bonus = Column(Integer, default=0)       # 속도 보너스
    combo_bonus = Column(Integer, default=0)       # 콤보 보너스
    rarity_bonus = Column(Integer, default=0)      # 희귀도 보너스
    difficulty_bonus = Column(Integer, default=0)  # 난이도 보너스
    time_bonus = Column(Integer, default=0)        # 시간대 보너스
    final_score = Column(Integer, default=0)       # 최종 점수
    
    # 메타데이터
    response_time = Column(Float)  # 응답 시간 (초)
    combo_count = Column(Integer, default=0)  # 현재 콤보 수
    turn_number = Column(Integer)
    round_number = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Step 2: 고급 점수 계산 서비스 구현

```python
# backend/services/advanced_scoring_service.py
import math
import re
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from models.word_statistics_model import WordStatistics
from services.korean_analyzer_service import KoreanAnalyzerService

class AdvancedScoringService:
    def __init__(self, db: Session):
        self.db = db
        self.korean_analyzer = KoreanAnalyzerService()
        
        # 점수 계산 설정
        self.BASE_SCORE_PER_CHAR = 10
        self.SPEED_BONUS_THRESHOLD = 15  # 15초 이하 빠른 응답
        self.MAX_SPEED_BONUS = 50
        self.COMBO_MULTIPLIER_BASE = 1.2
        self.MAX_COMBO_MULTIPLIER = 3.0
        
        # 희귀도 점수 구간
        self.RARITY_THRESHOLDS = {
            'very_common': (1000, 1.0),   # 1000회 이상 사용
            'common': (500, 1.2),         # 500-999회
            'uncommon': (100, 1.5),       # 100-499회
            'rare': (20, 2.0),            # 20-99회
            'very_rare': (5, 2.5),        # 5-19회
            'legendary': (1, 3.0)         # 1-4회
        }
    
    async def calculate_advanced_score(self, 
                                     word: str, 
                                     response_time: float,
                                     combo_count: int,
                                     turn_number: int,
                                     total_turns: int,
                                     round_number: int) -> Dict[str, int]:
        """
        고급 점수 계산 메인 함수
        
        Returns:
            Dict with score breakdown: {
                'base_score': int,
                'speed_bonus': int,
                'combo_bonus': int,
                'rarity_bonus': int,
                'difficulty_bonus': int,
                'time_bonus': int,
                'final_score': int,
                'multipliers': Dict[str, float]
            }
        """
        
        # 1. 기본 점수 계산
        base_score = len(word) * self.BASE_SCORE_PER_CHAR
        
        # 2. 속도 보너스 계산
        speed_bonus = self._calculate_speed_bonus(response_time)
        
        # 3. 단어 통계 조회/생성
        word_stats = await self._get_or_create_word_stats(word)
        
        # 4. 희귀도 보너스 계산
        rarity_multiplier, rarity_bonus = self._calculate_rarity_bonus(word_stats)
        
        # 5. 난이도 보너스 계산
        difficulty_multiplier, difficulty_bonus = self._calculate_difficulty_bonus(word, word_stats)
        
        # 6. 콤보 보너스 계산
        combo_multiplier, combo_bonus = self._calculate_combo_bonus(combo_count, base_score)
        
        # 7. 시간대 보너스 계산 (게임 후반부 가중치)
        time_multiplier, time_bonus = self._calculate_time_bonus(turn_number, total_turns, round_number)
        
        # 8. 최종 점수 계산
        bonus_sum = speed_bonus + rarity_bonus + difficulty_bonus + time_bonus
        total_multiplier = combo_multiplier * rarity_multiplier * difficulty_multiplier * time_multiplier
        final_score = int((base_score + bonus_sum) * total_multiplier)
        
        # 9. 단어 사용 통계 업데이트
        await self._update_word_usage(word_stats)
        
        return {
            'base_score': base_score,
            'speed_bonus': speed_bonus,
            'combo_bonus': combo_bonus,
            'rarity_bonus': rarity_bonus,
            'difficulty_bonus': difficulty_bonus,
            'time_bonus': time_bonus,
            'final_score': final_score,
            'multipliers': {
                'combo': combo_multiplier,
                'rarity': rarity_multiplier,
                'difficulty': difficulty_multiplier,
                'time': time_multiplier,
                'total': total_multiplier
            }
        }
    
    def _calculate_speed_bonus(self, response_time: float) -> int:
        """속도 보너스 계산"""
        if response_time >= self.SPEED_BONUS_THRESHOLD:
            return 0
        
        # 빠를수록 더 많은 보너스 (지수적 증가)
        time_saved = self.SPEED_BONUS_THRESHOLD - response_time
        bonus_ratio = time_saved / self.SPEED_BONUS_THRESHOLD
        speed_bonus = int(self.MAX_SPEED_BONUS * (bonus_ratio ** 1.5))
        
        return min(speed_bonus, self.MAX_SPEED_BONUS)
    
    def _calculate_combo_bonus(self, combo_count: int, base_score: int) -> tuple[float, int]:
        """콤보 보너스 계산"""
        if combo_count < 2:
            return 1.0, 0
        
        # 콤보 배수 계산 (2연속부터 시작, 최대 3배)
        combo_multiplier = min(
            self.COMBO_MULTIPLIER_BASE ** (combo_count - 1),
            self.MAX_COMBO_MULTIPLIER
        )
        combo_bonus = int(base_score * (combo_multiplier - 1))
        
        return combo_multiplier, combo_bonus
    
    async def _get_or_create_word_stats(self, word: str) -> WordStatistics:
        """단어 통계 조회 또는 생성"""
        word_stats = self.db.query(WordStatistics).filter(
            WordStatistics.word == word
        ).first()
        
        if not word_stats:
            # 새로운 단어인 경우 분석 후 생성
            analysis = self.korean_analyzer.analyze_word(word)
            word_stats = WordStatistics(
                word=word,
                syllable_count=analysis['syllable_count'],
                consonant_complexity=analysis['consonant_complexity'],
                vowel_complexity=analysis['vowel_complexity'],
                ending_difficulty=analysis['ending_difficulty'],
                rarity_score=analysis['initial_rarity_score']
            )
            self.db.add(word_stats)
            self.db.flush()  # ID 생성을 위해 flush
        
        return word_stats
    
    def _calculate_rarity_bonus(self, word_stats: WordStatistics) -> tuple[float, int]:
        """희귀도 보너스 계산"""
        usage_count = word_stats.usage_count
        
        # 사용 빈도에 따른 희귀도 등급 결정
        for rarity_level, (threshold, multiplier) in self.RARITY_THRESHOLDS.items():
            if usage_count >= threshold:
                rarity_multiplier = multiplier
                break
        else:
            rarity_multiplier = self.RARITY_THRESHOLDS['legendary'][1]
        
        # 희귀도 보너스는 기본 점수의 일정 비율
        base_score = len(word_stats.word) * self.BASE_SCORE_PER_CHAR
        rarity_bonus = int(base_score * (rarity_multiplier - 1))
        
        return rarity_multiplier, rarity_bonus
    
    def _calculate_difficulty_bonus(self, word: str, word_stats: WordStatistics) -> tuple[float, int]:
        """난이도 보너스 계산"""
        # 복합 난이도 점수 계산
        complexity_score = (
            word_stats.consonant_complexity * 0.3 +
            word_stats.vowel_complexity * 0.2 +
            word_stats.ending_difficulty * 0.5
        )
        
        # 난이도 배수 계산 (1.0 ~ 2.0)
        difficulty_multiplier = 1.0 + (complexity_score - 1.0) * 0.5
        difficulty_multiplier = max(1.0, min(2.0, difficulty_multiplier))
        
        # 난이도 보너스
        base_score = len(word) * self.BASE_SCORE_PER_CHAR
        difficulty_bonus = int(base_score * (difficulty_multiplier - 1))
        
        return difficulty_multiplier, difficulty_bonus
    
    def _calculate_time_bonus(self, turn_number: int, total_turns: int, round_number: int) -> tuple[float, int]:
        """시간대 보너스 계산 (게임 후반부 가중치)"""
        if total_turns <= 5:
            return 1.0, 0
        
        # 게임 진행률에 따른 가중치 (후반부로 갈수록 높아짐)
        progress_ratio = turn_number / total_turns
        if progress_ratio > 0.7:  # 70% 이후부터 보너스
            time_multiplier = 1.0 + (progress_ratio - 0.7) * 0.5  # 최대 15% 보너스
            base_score = self.BASE_SCORE_PER_CHAR * 3  # 적당한 기준 점수
            time_bonus = int(base_score * (time_multiplier - 1))
        else:
            time_multiplier = 1.0
            time_bonus = 0
        
        return time_multiplier, time_bonus
    
    async def _update_word_usage(self, word_stats: WordStatistics):
        """단어 사용 통계 업데이트"""
        word_stats.usage_count += 1
        word_stats.last_used = datetime.utcnow()
        
        # 사용 빈도에 따른 희귀도 점수 자동 조정
        if word_stats.usage_count in [5, 20, 100, 500, 1000]:
            word_stats.rarity_score = self._recalculate_rarity_score(word_stats.usage_count)
        
        self.db.commit()
    
    def _recalculate_rarity_score(self, usage_count: int) -> float:
        """사용 빈도에 따른 희귀도 점수 재계산"""
        if usage_count >= 1000:
            return 1.0  # 매우 흔함
        elif usage_count >= 500:
            return 1.2  # 흔함
        elif usage_count >= 100:
            return 1.5  # 보통
        elif usage_count >= 20:
            return 2.0  # 희귀
        elif usage_count >= 5:
            return 2.5  # 매우 희귀
        else:
            return 3.0  # 전설적
```

### Step 3: 한국어 단어 분석 서비스

```python
# backend/services/korean_analyzer_service.py
import re
from typing import Dict, List

class KoreanAnalyzerService:
    """한국어 단어 분석 및 난이도 계산 서비스"""
    
    def __init__(self):
        # 한글 자음/모음 복잡도 매핑
        self.CONSONANT_COMPLEXITY = {
            'ㄱ': 1.0, 'ㄴ': 1.0, 'ㄷ': 1.0, 'ㄹ': 1.2, 'ㅁ': 1.0,
            'ㅂ': 1.0, 'ㅅ': 1.1, 'ㅇ': 1.0, 'ㅈ': 1.2, 'ㅊ': 1.3,
            'ㅋ': 1.2, 'ㅌ': 1.2, 'ㅍ': 1.3, 'ㅎ': 1.1,
            'ㄲ': 1.5, 'ㄸ': 1.5, 'ㅃ': 1.5, 'ㅆ': 1.5, 'ㅉ': 1.5
        }
        
        self.VOWEL_COMPLEXITY = {
            'ㅏ': 1.0, 'ㅑ': 1.1, 'ㅓ': 1.0, 'ㅕ': 1.1, 'ㅗ': 1.0,
            'ㅛ': 1.1, 'ㅜ': 1.0, 'ㅠ': 1.1, 'ㅡ': 1.1, 'ㅣ': 1.0,
            'ㅐ': 1.2, 'ㅒ': 1.3, 'ㅔ': 1.2, 'ㅖ': 1.3, 'ㅘ': 1.4,
            'ㅙ': 1.5, 'ㅚ': 1.4, 'ㅝ': 1.4, 'ㅞ': 1.5, 'ㅟ': 1.4, 'ㅢ': 1.5
        }
        
        # 받침 난이도 (끝말잇기 연결 어려움 정도)
        self.ENDING_DIFFICULTY = {
            None: 1.0,      # 받침 없음
            'ㄴ': 1.2, 'ㄹ': 1.3, 'ㅁ': 1.4, 'ㅂ': 1.5, 'ㅅ': 1.6,
            'ㅇ': 1.1, 'ㄱ': 1.3, 'ㄷ': 1.4, 'ㅈ': 1.7, 'ㅊ': 1.8,
            'ㅋ': 1.9, 'ㅌ': 2.0, 'ㅍ': 2.1, 'ㅎ': 1.5,
            'ㄲ': 2.5, 'ㄸ': 2.5, 'ㅆ': 2.3, 'ㄺ': 3.0, 'ㄻ': 3.2,
            'ㄼ': 3.5, 'ㄽ': 3.8, 'ㄾ': 4.0, 'ㄿ': 4.2, 'ㅀ': 4.5, 'ㅄ': 3.0
        }
    
    def analyze_word(self, word: str) -> Dict[str, float]:
        """단어 분석 및 복잡도 계산"""
        syllables = self._decompose_word(word)
        
        consonant_complexity = self._calculate_consonant_complexity(syllables)
        vowel_complexity = self._calculate_vowel_complexity(syllables)
        ending_difficulty = self._calculate_ending_difficulty(word)
        
        return {
            'syllable_count': len(syllables),
            'consonant_complexity': consonant_complexity,
            'vowel_complexity': vowel_complexity,
            'ending_difficulty': ending_difficulty,
            'initial_rarity_score': 3.0  # 새 단어는 희귀한 것으로 시작
        }
    
    def _decompose_word(self, word: str) -> List[Dict]:
        """한글 단어를 음절별로 분해"""
        syllables = []
        
        for char in word:
            if '가' <= char <= '힣':  # 한글 음절인 경우
                code = ord(char) - 0xAC00
                initial = code // 588
                medial = (code % 588) // 28
                final = code % 28
                
                syllables.append({
                    'char': char,
                    'initial': initial,
                    'medial': medial,
                    'final': final if final != 0 else None
                })
            else:
                # 한글이 아닌 문자는 건너뛰기
                pass
        
        return syllables
    
    def _calculate_consonant_complexity(self, syllables: List[Dict]) -> float:
        """자음 복잡도 계산"""
        if not syllables:
            return 1.0
        
        total_complexity = 0
        for syllable in syllables:
            initial_char = chr(0x1100 + syllable['initial'])
            complexity = self.CONSONANT_COMPLEXITY.get(initial_char, 1.0)
            total_complexity += complexity
        
        return total_complexity / len(syllables)
    
    def _calculate_vowel_complexity(self, syllables: List[Dict]) -> float:
        """모음 복잡도 계산"""
        if not syllables:
            return 1.0
        
        total_complexity = 0
        for syllable in syllables:
            medial_char = chr(0x1161 + syllable['medial'])
            complexity = self.VOWEL_COMPLEXITY.get(medial_char, 1.0)
            total_complexity += complexity
        
        return total_complexity / len(syllables)
    
    def _calculate_ending_difficulty(self, word: str) -> float:
        """받침 난이도 계산 (끝말잇기 연결 어려움)"""
        if not word:
            return 1.0
        
        last_char = word[-1]
        if not ('가' <= last_char <= '힣'):
            return 1.0
        
        code = ord(last_char) - 0xAC00
        final = code % 28
        
        if final == 0:
            return self.ENDING_DIFFICULTY[None]
        else:
            final_char = chr(0x11A7 + final)
            return self.ENDING_DIFFICULTY.get(final_char, 2.0)
    
    def get_next_possible_initials(self, word: str) -> List[str]:
        """다음에 올 수 있는 시작 자음 목록"""
        if not word:
            return []
        
        last_char = word[-1]
        if not ('가' <= last_char <= '힣'):
            return []
        
        code = ord(last_char) - 0xAC00
        final = code % 28
        
        if final == 0:
            # 받침이 없는 경우, 마지막 모음의 마지막 소리로 시작
            medial = (code % 588) // 28
            medial_char = chr(0x1161 + medial)
            # 모음별 연결 가능한 자음 매핑 (간단화)
            return ['ㅇ']  # 일반적으로 'ㅇ'으로 시작하는 단어들
        else:
            # 받침이 있는 경우
            final_char = chr(0x11A7 + final)
            # 받침별 연결 가능한 자음 매핑
            consonant_map = {
                'ㄱ': ['ㄱ', 'ㅋ'], 'ㄴ': ['ㄴ'], 'ㄷ': ['ㄷ', 'ㅌ'],
                'ㄹ': ['ㄹ'], 'ㅁ': ['ㅁ'], 'ㅂ': ['ㅂ', 'ㅍ'],
                'ㅅ': ['ㅅ', 'ㅆ'], 'ㅇ': ['ㅇ'], 'ㅈ': ['ㅈ', 'ㅊ'],
                'ㅊ': ['ㅊ'], 'ㅋ': ['ㅋ'], 'ㅌ': ['ㅌ'], 'ㅍ': ['ㅍ'], 'ㅎ': ['ㅎ']
            }
            return consonant_map.get(final_char, ['ㅇ'])
```

### Step 4: Redis 게임 서비스 통합

```python
# backend/services/redis_game_service.py 수정
# 기존 파일에 추가할 메서드들

class RedisGameService:
    # ... 기존 코드 ...
    
    def __init__(self, redis_client):
        # ... 기존 초기화 코드 ...
        self.advanced_scoring = None  # 의존성 주입으로 설정
    
    def set_advanced_scoring_service(self, scoring_service):
        """고급 점수 서비스 설정"""
        self.advanced_scoring = scoring_service
    
    async def submit_word_with_advanced_scoring(self, room_id: int, guest_id: int, word: str) -> Dict[str, Any]:
        """고급 점수 계산이 포함된 단어 제출"""
        game_state = await self.get_game_state(room_id)
        if not game_state:
            return {"success": False, "error": "게임을 찾을 수 없습니다"}
        
        if game_state.get('current_player_id') != guest_id:
            return {"success": False, "error": "당신의 턴이 아닙니다"}
        
        # 기존 단어 검증
        if not self.validate_word_chain(word, game_state.get('last_character', '')):
            return {"success": False, "error": "단어 연결이 올바르지 않습니다"}
        
        if word in game_state.get('used_words', []):
            return {"success": False, "error": "이미 사용된 단어입니다"}
        
        # 응답 시간 계산
        turn_start_time = game_state.get('turn_start_time')
        current_time = datetime.utcnow().timestamp()
        response_time = current_time - turn_start_time if turn_start_time else 30
        
        # 플레이어 통계 조회
        player_stats = await self.get_player_stats(room_id, guest_id)
        combo_count = player_stats.get('current_combo', 0)
        
        # 고급 점수 계산
        if self.advanced_scoring:
            score_breakdown = await self.advanced_scoring.calculate_advanced_score(
                word=word,
                response_time=response_time,
                combo_count=combo_count,
                turn_number=game_state.get('turn_number', 1),
                total_turns=len(game_state.get('participants', [])) * game_state.get('max_rounds', 10),
                round_number=game_state.get('round_number', 1)
            )
            
            final_score = score_breakdown['final_score']
            
            # 점수 히스토리 저장 (Redis)
            score_history_key = f"game:{room_id}:scores:{guest_id}"
            await self.redis.lpush(score_history_key, json.dumps({
                **score_breakdown,
                'word': word,
                'response_time': response_time,
                'timestamp': current_time
            }))
            await self.redis.expire(score_history_key, self.GAME_TTL)
        else:
            # 기존 점수 계산 폴백
            final_score = len(word) * 10
            score_breakdown = {
                'base_score': final_score,
                'final_score': final_score,
                'multipliers': {'total': 1.0}
            }
        
        # 플레이어 통계 업데이트
        player_stats['score'] = player_stats.get('score', 0) + final_score
        player_stats['words_submitted'] += 1
        player_stats['total_response_time'] += response_time
        
        # 콤보 계산
        if response_time <= 15:  # 빠른 응답
            player_stats['current_combo'] = combo_count + 1
            player_stats['max_combo'] = max(player_stats.get('max_combo', 0), player_stats['current_combo'])
        else:
            player_stats['current_combo'] = 0
        
        # 통계 저장
        await self.update_player_stats(room_id, guest_id, player_stats)
        
        # 게임 상태 업데이트
        await self._update_game_state_after_word(room_id, word, guest_id, game_state)
        
        return {
            "success": True,
            "score_breakdown": score_breakdown,
            "new_total_score": player_stats['score'],
            "combo_count": player_stats['current_combo']
        }
```

### Step 5: 프론트엔드 점수 표시 컴포넌트

```javascript
// frontend/src/components/ScoreBreakdown.js
import React from 'react';

const ScoreBreakdown = ({ scoreData, isVisible, onClose }) => {
    if (!isVisible || !scoreData) return null;
    
    const {
        base_score,
        speed_bonus,
        combo_bonus,
        rarity_bonus,
        difficulty_bonus,
        time_bonus,
        final_score,
        multipliers
    } = scoreData;
    
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div className="text-center mb-4">
                    <h3 className="text-2xl font-bold text-gray-800">점수 분석</h3>
                    <div className="text-4xl font-bold text-purple-600 mt-2">
                        {final_score.toLocaleString()}점
                    </div>
                </div>
                
                <div className="space-y-3 mb-6">
                    <ScoreItem label="기본 점수" value={base_score} icon="📝" />
                    {speed_bonus > 0 && (
                        <ScoreItem label="속도 보너스" value={speed_bonus} icon="⚡" bonus />
                    )}
                    {combo_bonus > 0 && (
                        <ScoreItem label="콤보 보너스" value={combo_bonus} icon="🔥" bonus />
                    )}
                    {rarity_bonus > 0 && (
                        <ScoreItem label="희귀도 보너스" value={rarity_bonus} icon="💎" bonus />
                    )}
                    {difficulty_bonus > 0 && (
                        <ScoreItem label="난이도 보너스" value={difficulty_bonus} icon="🎯" bonus />
                    )}
                    {time_bonus > 0 && (
                        <ScoreItem label="시간대 보너스" value={time_bonus} icon="⏰" bonus />
                    )}
                </div>
                
                {multipliers.total > 1 && (
                    <div className="border-t pt-4 mb-4">
                        <div className="text-center text-sm text-gray-600">
                            총 배수: {multipliers.total.toFixed(2)}x
                        </div>
                    </div>
                )}
                
                <button
                    onClick={onClose}
                    className="w-full py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
                >
                    확인
                </button>
            </div>
        </div>
    );
};

const ScoreItem = ({ label, value, icon, bonus = false }) => (
    <div className={`flex justify-between items-center p-2 rounded ${bonus ? 'bg-green-50' : 'bg-gray-50'}`}>
        <span className="flex items-center">
            <span className="mr-2">{icon}</span>
            <span className={bonus ? 'text-green-700 font-medium' : 'text-gray-700'}>{label}</span>
        </span>
        <span className={`font-bold ${bonus ? 'text-green-600' : 'text-gray-800'}`}>
            +{value.toLocaleString()}
        </span>
    </div>
);

export default ScoreBreakdown;
```

### Step 6: 실시간 점수 업데이트

```javascript
// frontend/src/Pages/InGame/hooks/useWordChain.js 수정
// 기존 파일에 추가할 부분

const useWordChain = () => {
    // ... 기존 상태 ...
    const [scoreBreakdown, setScoreBreakdown] = useState(null);
    const [showScoreModal, setShowScoreModal] = useState(false);
    const [playerStats, setPlayerStats] = useState({});
    
    // WebSocket 메시지 처리에 추가
    useEffect(() => {
        const handleGameMessage = (data) => {
            if (data.type === 'word_submitted_advanced') {
                // 고급 점수 정보 처리
                if (data.score_breakdown) {
                    setScoreBreakdown(data.score_breakdown);
                    setShowScoreModal(true);
                    
                    // 3초 후 자동 닫기
                    setTimeout(() => setShowScoreModal(false), 3000);
                }
                
                // 플레이어 통계 업데이트
                if (data.player_stats) {
                    setPlayerStats(prev => ({
                        ...prev,
                        [data.guest_id]: data.player_stats
                    }));
                }
            }
        };
        
        // WebSocket 메시지 리스너 등록
        // ... 기존 코드 ...
    }, []);
    
    return {
        // ... 기존 반환값 ...
        scoreBreakdown,
        showScoreModal,
        setShowScoreModal,
        playerStats
    };
};
```

---

## 🎮 사용자 경험 개선

### 점수 애니메이션
```css
/* frontend/src/styles/score-animations.css */
@keyframes scorePopup {
    0% {
        transform: scale(0) translateY(20px);
        opacity: 0;
    }
    50% {
        transform: scale(1.2) translateY(-10px);
        opacity: 1;
    }
    100% {
        transform: scale(1) translateY(0);
        opacity: 1;
    }
}

@keyframes comboGlow {
    0%, 100% {
        box-shadow: 0 0 5px rgba(255, 193, 7, 0.5);
    }
    50% {
        box-shadow: 0 0 20px rgba(255, 193, 7, 0.8), 0 0 30px rgba(255, 193, 7, 0.6);
    }
}

.score-popup {
    animation: scorePopup 0.6s ease-out;
}

.combo-indicator {
    animation: comboGlow 1s ease-in-out infinite;
}

.rare-word-effect {
    background: linear-gradient(45deg, #FFD700, #FFA500);
    animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
    0%, 100% { background-position: -200% 0; }
    50% { background-position: 200% 0; }
}
```

### 실시간 통계 표시
```javascript
// frontend/src/components/GameStats.js
const GameStats = ({ playerStats, currentUserId }) => {
    const userStats = playerStats[currentUserId] || {};
    
    return (
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-white">
            <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                    <div className="text-2xl font-bold">{userStats.score?.toLocaleString() || 0}</div>
                    <div className="text-sm opacity-75">총 점수</div>
                </div>
                <div>
                    <div className="text-2xl font-bold">{userStats.current_combo || 0}</div>
                    <div className="text-sm opacity-75">현재 콤보</div>
                </div>
                <div>
                    <div className="text-lg font-semibold">{userStats.words_submitted || 0}</div>
                    <div className="text-sm opacity-75">제출한 단어</div>
                </div>
                <div>
                    <div className="text-lg font-semibold">
                        {userStats.average_response_time?.toFixed(1) || 0}초
                    </div>
                    <div className="text-sm opacity-75">평균 응답시간</div>
                </div>
            </div>
            
            {userStats.current_combo > 2 && (
                <div className="mt-3 text-center">
                    <div className="combo-indicator bg-yellow-500 text-black px-3 py-1 rounded-full text-sm font-bold">
                        🔥 {userStats.current_combo} 콤보!
                    </div>
                </div>
            )}
        </div>
    );
};
```

이 고급 점수 시스템을 통해 플레이어들은 더욱 전략적이고 흥미진진한 게임 경험을 할 수 있으며, 단순한 끝말잇기를 넘어서 깊이 있는 게임플레이를 즐길 수 있습니다.