"""
점수 계산 서비스
기본 점수, 속도 보너스, 콤보 시스템, 단어 희귀도 보너스
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from services.word_validator import WordInfo
from redis_models import WordChainState, GamePlayer

logger = logging.getLogger(__name__)


class ScoreType(str, Enum):
    """점수 타입"""
    BASE = "base"                    # 기본 점수
    SPEED_BONUS = "speed_bonus"      # 속도 보너스
    COMBO_BONUS = "combo_bonus"      # 콤보 보너스
    RARITY_BONUS = "rarity_bonus"    # 희귀도 보너스
    LENGTH_BONUS = "length_bonus"    # 길이 보너스
    DIFFICULTY_BONUS = "difficulty_bonus"  # 난이도 보너스


@dataclass
class ScoreBreakdown:
    """점수 세부 내역"""
    base_score: int = 0
    speed_bonus: int = 0
    combo_bonus: int = 0
    rarity_bonus: int = 0
    length_bonus: int = 0
    difficulty_bonus: int = 0
    item_bonus: int = 0
    total_score: int = 0
    response_time_seconds: float = 0.0
    combo_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "base_score": self.base_score,
            "speed_bonus": self.speed_bonus,
            "combo_bonus": self.combo_bonus,
            "rarity_bonus": self.rarity_bonus,
            "length_bonus": self.length_bonus,
            "difficulty_bonus": self.difficulty_bonus,
            "item_bonus": self.item_bonus,
            "total_score": self.total_score,
            "response_time_seconds": self.response_time_seconds,
            "combo_count": self.combo_count
        }


@dataclass
class ScoreConfig:
    """점수 계산 설정"""
    base_multiplier: float = 10.0        # 기본 배수
    max_speed_bonus: int = 50           # 최대 속도 보너스
    speed_bonus_multiplier: float = 2.0  # 속도 보너스 배수
    combo_bonus_per_count: int = 10     # 콤보당 보너스 점수
    max_combo_multiplier: float = 3.0   # 최대 콤보 배수
    length_bonus_threshold: int = 4     # 길이 보너스 시작 글자 수
    length_bonus_per_char: int = 5      # 글자당 길이 보너스
    rarity_bonus_multiplier: float = 0.5  # 희귀도 보너스 배수
    turn_time_limit: int = 30           # 턴 제한 시간 (초)


class ScoreCalculator:
    """점수 계산기"""
    
    def __init__(self, config: Optional[ScoreConfig] = None):
        self.config = config or ScoreConfig()
    
    def calculate_word_score(self, word_info: WordInfo, response_time_seconds: float, 
                           word_chain: WordChainState, item_multiplier: float = 1.0) -> ScoreBreakdown:
        """단어 점수 계산"""
        breakdown = ScoreBreakdown()
        breakdown.response_time_seconds = response_time_seconds
        breakdown.combo_count = word_chain.combo_count
        
        # 1. 기본 점수 (글자 수 × 기본 배수)
        breakdown.base_score = int(word_info.length * self.config.base_multiplier)
        
        # 2. 난이도 보너스
        breakdown.difficulty_bonus = int(word_info.difficulty * 5)
        
        # 3. 속도 보너스 (빠른 답변일수록 높은 점수)
        if response_time_seconds < self.config.turn_time_limit:
            remaining_time = self.config.turn_time_limit - response_time_seconds
            breakdown.speed_bonus = min(
                int(remaining_time * self.config.speed_bonus_multiplier),
                self.config.max_speed_bonus
            )
        
        # 4. 콤보 보너스
        combo_multiplier = min(
            1 + (word_chain.combo_count * 0.1),
            self.config.max_combo_multiplier
        )
        breakdown.combo_bonus = int(word_chain.combo_count * self.config.combo_bonus_per_count)
        
        # 5. 희귀도 보너스 (빈도 점수의 역수 활용)
        if word_info.frequency_score > 0:
            # 빈도가 낮을수록 높은 보너스
            rarity_factor = max(0, 100 - word_info.frequency_score)
            breakdown.rarity_bonus = int(rarity_factor * self.config.rarity_bonus_multiplier)
        
        # 6. 길이 보너스 (긴 단어 추가 점수)
        if word_info.length >= self.config.length_bonus_threshold:
            extra_chars = word_info.length - self.config.length_bonus_threshold
            breakdown.length_bonus = extra_chars * self.config.length_bonus_per_char
        
        # 7. 아이템 보너스 적용
        if item_multiplier != 1.0:
            base_total = breakdown.base_score + breakdown.difficulty_bonus + breakdown.speed_bonus
            breakdown.item_bonus = int(base_total * (item_multiplier - 1.0))
        
        # 8. 총점 계산 (콤보 배수 적용)
        subtotal = (breakdown.base_score + breakdown.difficulty_bonus + breakdown.speed_bonus + 
                   breakdown.rarity_bonus + breakdown.length_bonus + breakdown.item_bonus)
        
        breakdown.total_score = int(subtotal * combo_multiplier) + breakdown.combo_bonus
        
        logger.debug(f"점수 계산 완료: word={word_info.word}, total={breakdown.total_score}")
        return breakdown
    
    def calculate_game_bonus(self, player: GamePlayer, final_rank: int, total_players: int) -> Dict[str, int]:
        """게임 종료 시 추가 보너스 계산"""
        bonus = {
            "rank_bonus": 0,
            "participation_bonus": 0,
            "consistency_bonus": 0,
            "total_bonus": 0
        }
        
        # 순위 보너스
        if final_rank == 1:
            bonus["rank_bonus"] = 200  # 1등 보너스
        elif final_rank == 2:
            bonus["rank_bonus"] = 100  # 2등 보너스
        elif final_rank == 3:
            bonus["rank_bonus"] = 50   # 3등 보너스
        
        # 참여 보너스 (제출한 단어 수에 비례)
        bonus["participation_bonus"] = player.words_submitted * 5
        
        # 일관성 보너스 (최대 콤보에 따라)
        bonus["consistency_bonus"] = player.max_combo * 10
        
        bonus["total_bonus"] = sum(bonus.values()) - bonus["total_bonus"]  # total_bonus 제외하고 합계
        
        return bonus
    
    def calculate_item_multiplier(self, active_items: List[Dict[str, Any]]) -> float:
        """활성 아이템들의 점수 배수 계산"""
        total_multiplier = 1.0
        
        for item in active_items:
            if item.get("effect_type") == "score_multiplier":
                multiplier = item.get("effect_value", {}).get("multiplier", 1.0)
                total_multiplier *= multiplier
        
        # 최대 5배까지 제한
        return min(total_multiplier, 5.0)
    
    def get_rank_from_scores(self, scores: List[int]) -> Dict[int, int]:
        """점수 목록으로부터 순위 계산"""
        # 점수와 인덱스를 함께 저장
        score_with_index = [(score, i) for i, score in enumerate(scores)]
        
        # 점수 기준으로 내림차순 정렬
        score_with_index.sort(key=lambda x: x[0], reverse=True)
        
        # 순위 할당
        ranks = {}
        current_rank = 1
        
        for i, (score, original_index) in enumerate(score_with_index):
            if i > 0 and score != score_with_index[i-1][0]:
                current_rank = i + 1
            ranks[original_index] = current_rank
        
        return ranks
    
    def calculate_accuracy_bonus(self, correct_words: int, total_attempts: int) -> int:
        """정확도 보너스 계산"""
        if total_attempts == 0:
            return 0
        
        accuracy = correct_words / total_attempts
        
        if accuracy >= 0.9:
            return 100
        elif accuracy >= 0.8:
            return 50
        elif accuracy >= 0.7:
            return 25
        else:
            return 0
    
    def calculate_time_efficiency_bonus(self, total_time_used: float, max_possible_time: float) -> int:
        """시간 효율성 보너스 계산"""
        if max_possible_time <= 0:
            return 0
        
        efficiency = 1.0 - (total_time_used / max_possible_time)
        
        # 50% 이상 시간을 절약한 경우에만 보너스
        if efficiency >= 0.5:
            return int(efficiency * 200)
        else:
            return 0
    
    def get_score_analysis(self, breakdown: ScoreBreakdown) -> Dict[str, Any]:
        """점수 분석 정보 제공"""
        analysis = {
            "performance_rating": "보통",
            "strong_points": [],
            "improvement_tips": []
        }
        
        # 성과 평가
        if breakdown.total_score >= 100:
            analysis["performance_rating"] = "우수"
        elif breakdown.total_score >= 50:
            analysis["performance_rating"] = "양호"
        elif breakdown.total_score < 20:
            analysis["performance_rating"] = "개선 필요"
        
        # 강점 분석
        if breakdown.speed_bonus >= 30:
            analysis["strong_points"].append("빠른 반응속도")
        
        if breakdown.combo_count >= 5:
            analysis["strong_points"].append("높은 연속성")
        
        if breakdown.rarity_bonus >= 20:
            analysis["strong_points"].append("희귀 단어 활용")
        
        if breakdown.length_bonus >= 15:
            analysis["strong_points"].append("긴 단어 선호")
        
        # 개선 팁
        if breakdown.speed_bonus < 10:
            analysis["improvement_tips"].append("더 빠른 답변을 시도해보세요")
        
        if breakdown.combo_count < 3:
            analysis["improvement_tips"].append("연속으로 정답을 맞춰 콤보를 높여보세요")
        
        if breakdown.rarity_bonus < 10:
            analysis["improvement_tips"].append("다양한 단어를 사용해보세요")
        
        return analysis
    
    def export_score_history(self, game_history: List[ScoreBreakdown]) -> Dict[str, Any]:
        """점수 기록 내보내기"""
        if not game_history:
            return {}
        
        total_games = len(game_history)
        total_score = sum(score.total_score for score in game_history)
        avg_score = total_score / total_games
        
        avg_response_time = sum(score.response_time_seconds for score in game_history) / total_games
        max_combo = max(score.combo_count for score in game_history)
        
        return {
            "total_games": total_games,
            "total_score": total_score,
            "average_score": round(avg_score, 2),
            "average_response_time": round(avg_response_time, 2),
            "max_combo_achieved": max_combo,
            "score_trend": [score.total_score for score in game_history[-10:]],  # 최근 10게임
            "performance_summary": {
                "best_game": max(score.total_score for score in game_history),
                "worst_game": min(score.total_score for score in game_history),
                "consistency": self._calculate_consistency(game_history)
            }
        }
    
    def _calculate_consistency(self, game_history: List[ScoreBreakdown]) -> float:
        """점수 일관성 계산 (표준편차 기반)"""
        if len(game_history) < 2:
            return 1.0
        
        scores = [score.total_score for score in game_history]
        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # 표준편차가 낮을수록 일관성이 높음 (0~1 스케일)
        consistency = max(0, 1 - (std_dev / max(mean, 1)))
        return round(consistency, 3)


# 전역 점수 계산기 인스턴스
score_calculator = ScoreCalculator()


def get_score_calculator() -> ScoreCalculator:
    """점수 계산기 의존성"""
    return score_calculator


def create_custom_score_calculator(config: ScoreConfig) -> ScoreCalculator:
    """커스텀 설정으로 점수 계산기 생성"""
    return ScoreCalculator(config)