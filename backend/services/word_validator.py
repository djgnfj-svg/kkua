"""
단어 검증 서비스
한국어 단어 유효성 검증, 끝말잇기 규칙, 중복 확인, Redis 캐싱
"""

import re
import logging
from typing import Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from database import get_db, get_redis
from models.dictionary_models import KoreanDictionary
from redis_models import WordChainState
from sqlalchemy import select
import redis
import json

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    """단어 검증 결과"""
    VALID = "valid"
    INVALID_WORD = "invalid_word"          # 사전에 없는 단어
    INVALID_CHAIN = "invalid_chain"        # 끝말잇기 규칙 위반
    ALREADY_USED = "already_used"          # 이미 사용된 단어
    TOO_SHORT = "too_short"               # 너무 짧음
    TOO_LONG = "too_long"                 # 너무 김
    FORBIDDEN = "forbidden"               # 금지된 단어
    INVALID_CHARACTER = "invalid_character" # 유효하지 않은 문자


@dataclass
class WordInfo:
    """단어 정보"""
    word: str
    definition: str
    difficulty: int
    frequency_score: int
    first_char: str
    last_char: str
    length: int
    is_valid: bool


@dataclass
class ValidationResponse:
    """검증 응답"""
    result: ValidationResult
    message: str
    word_info: Optional[WordInfo] = None
    score_info: Optional[Dict[str, Any]] = None


class WordValidator:
    """단어 검증기"""
    
    def __init__(self):
        self.redis_client = get_redis()
        
        # 설정
        self.min_word_length = 2
        self.max_word_length = 10
        self.cache_ttl = 3600  # 1시간
        
        # 금지된 단어 패턴 (욕설, 비속어)
        self.forbidden_patterns = [
            r'.*시발.*', r'.*씨발.*', r'.*개새.*', r'.*병신.*',
            r'.*미친.*', r'.*바보.*', r'.*멍청.*', r'.*죽어.*'
        ]
        
        # 한국어 문자 패턴
        self.korean_pattern = re.compile(r'^[가-힣]+$')
        
        # Redis 키 접두사
        self.word_cache_prefix = "word_cache:"
        self.chain_cache_prefix = "chain_cache:"
    
    async def validate_word(self, word: str, word_chain: WordChainState, used_words: Set[str]) -> ValidationResponse:
        """단어 종합 검증"""
        try:
            # 1. 기본 검증
            basic_result = self._validate_basic_rules(word)
            if basic_result.result != ValidationResult.VALID:
                return basic_result
            
            # 2. 끝말잇기 규칙 검증
            chain_result = self._validate_chain_rule(word, word_chain)
            if chain_result.result != ValidationResult.VALID:
                return chain_result
            
            # 3. 중복 사용 검증
            if word in used_words:
                return ValidationResponse(
                    result=ValidationResult.ALREADY_USED,
                    message="이미 사용된 단어입니다"
                )
            
            # 4. 사전 검증 (캐시 우선)
            word_info = await self._get_word_info(word)
            if not word_info or not word_info.is_valid:
                return ValidationResponse(
                    result=ValidationResult.INVALID_WORD,
                    message="사전에 없는 단어입니다"
                )
            
            # 5. 점수 정보 계산
            score_info = self._calculate_score_info(word_info, word_chain)
            
            return ValidationResponse(
                result=ValidationResult.VALID,
                message="유효한 단어입니다",
                word_info=word_info,
                score_info=score_info
            )
            
        except Exception as e:
            logger.error(f"단어 검증 중 오류: {e}")
            return ValidationResponse(
                result=ValidationResult.INVALID_WORD,
                message="단어 검증 중 오류가 발생했습니다"
            )
    
    def _validate_basic_rules(self, word: str) -> ValidationResponse:
        """기본 규칙 검증"""
        # 길이 검증
        if len(word) < self.min_word_length:
            return ValidationResponse(
                result=ValidationResult.TOO_SHORT,
                message=f"단어는 최소 {self.min_word_length}글자 이상이어야 합니다"
            )
        
        if len(word) > self.max_word_length:
            return ValidationResponse(
                result=ValidationResult.TOO_LONG,
                message=f"단어는 최대 {self.max_word_length}글자까지 가능합니다"
            )
        
        # 한국어 문자 검증
        if not self.korean_pattern.match(word):
            return ValidationResponse(
                result=ValidationResult.INVALID_CHARACTER,
                message="한국어만 사용 가능합니다"
            )
        
        # 금지어 검증
        for pattern in self.forbidden_patterns:
            if re.match(pattern, word):
                return ValidationResponse(
                    result=ValidationResult.FORBIDDEN,
                    message="사용할 수 없는 단어입니다"
                )
        
        return ValidationResponse(
            result=ValidationResult.VALID,
            message="기본 규칙 통과"
        )
    
    def _validate_chain_rule(self, word: str, word_chain: WordChainState) -> ValidationResponse:
        """끝말잇기 규칙 검증"""
        if not word_chain.last_char:
            # 첫 단어인 경우 통과
            return ValidationResponse(
                result=ValidationResult.VALID,
                message="첫 단어"
            )
        
        if word[0] != word_chain.last_char:
            return ValidationResponse(
                result=ValidationResult.INVALID_CHAIN,
                message=f"'{word_chain.last_char}'(으)로 시작하는 단어여야 합니다"
            )
        
        return ValidationResponse(
            result=ValidationResult.VALID,
            message="끝말잇기 규칙 통과"
        )
    
    async def _get_word_info(self, word: str) -> Optional[WordInfo]:
        """단어 정보 조회 (캐시 우선)"""
        try:
            # Redis 캐시에서 조회
            cache_key = f"{self.word_cache_prefix}{word}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                word_data = json.loads(cached_data)
                return WordInfo(**word_data)
            
            # 데이터베이스에서 조회
            db = next(get_db())
            result = db.execute(
                select(KoreanDictionary).where(KoreanDictionary.word == word)
            )
            dict_entry = result.scalar_one_or_none()
            
            if dict_entry:
                word_info = WordInfo(
                    word=dict_entry.word,
                    definition=dict_entry.definition or "",
                    difficulty=dict_entry.difficulty,
                    frequency_score=dict_entry.frequency_score,
                    first_char=dict_entry.first_char,
                    last_char=dict_entry.last_char,
                    length=len(dict_entry.word),
                    is_valid=True
                )
                
                # Redis에 캐시
                cache_data = {
                    "word": word_info.word,
                    "definition": word_info.definition,
                    "difficulty": word_info.difficulty,
                    "frequency_score": word_info.frequency_score,
                    "first_char": word_info.first_char,
                    "last_char": word_info.last_char,
                    "length": word_info.length,
                    "is_valid": word_info.is_valid
                }
                
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(cache_data, ensure_ascii=False)
                )
                
                return word_info
            
            # 없는 단어도 캐시 (무효한 단어로)
            invalid_info = WordInfo(
                word=word,
                definition="",
                difficulty=0,
                frequency_score=0,
                first_char=word[0] if word else "",
                last_char=word[-1] if word else "",
                length=len(word),
                is_valid=False
            )
            
            cache_data = {
                "word": invalid_info.word,
                "definition": invalid_info.definition,
                "difficulty": invalid_info.difficulty,
                "frequency_score": invalid_info.frequency_score,
                "first_char": invalid_info.first_char,
                "last_char": invalid_info.last_char,
                "length": invalid_info.length,
                "is_valid": invalid_info.is_valid
            }
            
            # 무효한 단어는 짧은 시간만 캐시
            self.redis_client.setex(
                cache_key,
                300,  # 5분
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            return invalid_info
            
        except Exception as e:
            logger.error(f"단어 정보 조회 중 오류: {e}")
            return None
    
    def _calculate_score_info(self, word_info: WordInfo, word_chain: WordChainState) -> Dict[str, Any]:
        """점수 정보 계산"""
        # 기본 점수 = 글자 수 × 난이도
        base_score = word_info.length * word_info.difficulty
        
        # 희귀도 보너스 (빈도 점수 역수)
        rarity_bonus = max(0, 100 - word_info.frequency_score)
        
        # 길이 보너스 (긴 단어일수록 추가 점수)
        length_bonus = max(0, (word_info.length - 3) * 5)
        
        # 현재 콤보 보너스 정보
        combo_multiplier = min(1 + (word_chain.combo_count * 0.1), 3.0)  # 최대 3배
        
        return {
            "base_score": base_score,
            "rarity_bonus": rarity_bonus,
            "length_bonus": length_bonus,
            "combo_multiplier": combo_multiplier,
            "estimated_total": int((base_score + rarity_bonus + length_bonus) * combo_multiplier)
        }
    
    async def get_word_hints(self, last_char: str, count: int = 3) -> List[str]:
        """다음에 올 수 있는 단어 힌트"""
        try:
            # Redis 캐시 확인
            cache_key = f"{self.chain_cache_prefix}{last_char}:{count}"
            cached_hints = self.redis_client.get(cache_key)
            
            if cached_hints:
                return json.loads(cached_hints)
            
            # 데이터베이스에서 조회
            db = next(get_db())
            result = db.execute(
                select(KoreanDictionary.word)
                .where(KoreanDictionary.first_char == last_char)
                .order_by(KoreanDictionary.frequency_score.desc())
                .limit(count * 2)  # 여분으로 더 조회
            )
            
            words = [row[0] for row in result.fetchall()]
            
            # 무작위로 섞어서 힌트 개수만큼 반환
            import random
            random.shuffle(words)
            hints = words[:count]
            
            # Redis에 캐시 (10분)
            self.redis_client.setex(
                cache_key,
                600,
                json.dumps(hints, ensure_ascii=False)
            )
            
            return hints
            
        except Exception as e:
            logger.error(f"단어 힌트 조회 중 오류: {e}")
            return []
    
    async def get_possible_words_count(self, last_char: str) -> int:
        """해당 글자로 시작하는 가능한 단어 개수"""
        try:
            # Redis 캐시 확인
            cache_key = f"count:{last_char}"
            cached_count = self.redis_client.get(cache_key)
            
            if cached_count:
                return int(cached_count)
            
            # 데이터베이스에서 조회
            db = next(get_db())
            result = db.execute(
                select(KoreanDictionary.word_id)
                .where(KoreanDictionary.first_char == last_char)
            )
            
            count = len(result.fetchall())
            
            # Redis에 캐시 (1시간)
            self.redis_client.setex(cache_key, 3600, str(count))
            
            return count
            
        except Exception as e:
            logger.error(f"가능한 단어 개수 조회 중 오류: {e}")
            return 0
    
    async def is_ending_character(self, char: str) -> bool:
        """게임 종료 글자 확인 (다음 단어가 없는 글자)"""
        count = await self.get_possible_words_count(char)
        return count == 0
    
    def clear_word_cache(self, word: Optional[str] = None):
        """단어 캐시 삭제"""
        try:
            if word:
                # 특정 단어 캐시 삭제
                cache_key = f"{self.word_cache_prefix}{word}"
                self.redis_client.delete(cache_key)
            else:
                # 모든 단어 캐시 삭제
                pattern = f"{self.word_cache_prefix}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    
        except Exception as e:
            logger.error(f"캐시 삭제 중 오류: {e}")
    
    async def preload_common_words(self, limit: int = 1000):
        """자주 사용되는 단어들을 사전에 캐시"""
        try:
            db = next(get_db())
            result = db.execute(
                select(KoreanDictionary)
                .order_by(KoreanDictionary.frequency_score.desc())
                .limit(limit)
            )
            
            words = result.fetchall()
            
            for dict_entry in words:
                word_info = WordInfo(
                    word=dict_entry.word,
                    definition=dict_entry.definition or "",
                    difficulty=dict_entry.difficulty,
                    frequency_score=dict_entry.frequency_score,
                    first_char=dict_entry.first_char,
                    last_char=dict_entry.last_char,
                    length=len(dict_entry.word),
                    is_valid=True
                )
                
                cache_key = f"{self.word_cache_prefix}{dict_entry.word}"
                cache_data = {
                    "word": word_info.word,
                    "definition": word_info.definition,
                    "difficulty": word_info.difficulty,
                    "frequency_score": word_info.frequency_score,
                    "first_char": word_info.first_char,
                    "last_char": word_info.last_char,
                    "length": word_info.length,
                    "is_valid": word_info.is_valid
                }
                
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(cache_data, ensure_ascii=False)
                )
            
            logger.info(f"자주 사용되는 {len(words)}개 단어를 캐시에 미리 로드했습니다")
            
        except Exception as e:
            logger.error(f"단어 사전 로드 중 오류: {e}")


# 전역 단어 검증기 인스턴스
word_validator = WordValidator()


def get_word_validator() -> WordValidator:
    """단어 검증기 의존성"""
    return word_validator