"""
고급 점수 계산 시스템
속도 보너스, 콤보, 희귀도 반영
"""

import math
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AdvancedScoreCalculator:
    """고급 점수 계산기"""
    
    def __init__(self):
        # 기본 점수 설정
        self.BASE_SCORE_PER_CHAR = 10
        
        # 속도 보너스 설정
        self.SPEED_BONUS_THRESHOLD = 5.0  # 5초 이하 = 빠름
        self.MAX_SPEED_BONUS = 2.0  # 최대 2배 보너스
        
        # 콤보 설정
        self.COMBO_THRESHOLD = 3  # 3연속부터 콤보
        self.MAX_COMBO_MULTIPLIER = 3.0  # 최대 3배
        
        # 희귀도 점수 (글자 수 기반)
        self.RARITY_SCORES = {
            2: 1.0,  # 2글자 = 기본
            3: 1.2,  # 3글자 = 1.2배
            4: 1.5,  # 4글자 = 1.5배
            5: 2.0,  # 5글자 = 2배
            6: 2.5,  # 6글자 = 2.5배
            7: 3.0,  # 7글자 = 3배
            8: 4.0,  # 8글자 이상 = 4배
        }
        
        # 특수 단어 보너스
        self.SPECIAL_WORD_PATTERNS = {
            '어려운단어': 1.5,  # 어려운 한국어 단어들
            '고급어휘': 2.0,   # 고급 어휘
        }
    
    def calculate_word_score(
        self, 
        word: str, 
        response_time: float, 
        consecutive_success: int = 0,
        game_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        단어 점수 계산
        
        Args:
            word: 제출된 단어
            response_time: 응답 시간 (초)
            consecutive_success: 연속 성공 횟수
            game_context: 게임 컨텍스트 정보
        
        Returns:
            점수 상세 정보
        """
        # 기본 점수
        base_score = len(word) * self.BASE_SCORE_PER_CHAR
        
        # 희귀도 보너스
        rarity_multiplier = self._calculate_rarity_multiplier(word)
        
        # 속도 보너스
        speed_multiplier = self._calculate_speed_multiplier(response_time)
        
        # 콤보 보너스
        combo_multiplier = self._calculate_combo_multiplier(consecutive_success)
        
        # 특수 단어 보너스
        special_multiplier = self._calculate_special_word_multiplier(word)
        
        # 총 배수 계산
        total_multiplier = (
            rarity_multiplier * 
            speed_multiplier * 
            combo_multiplier * 
            special_multiplier
        )
        
        # 최종 점수
        final_score = int(base_score * total_multiplier)
        
        return {
            'base_score': base_score,
            'final_score': final_score,
            'total_multiplier': round(total_multiplier, 2),
            'breakdown': {
                'rarity_multiplier': round(rarity_multiplier, 2),
                'speed_multiplier': round(speed_multiplier, 2),
                'combo_multiplier': round(combo_multiplier, 2),
                'special_multiplier': round(special_multiplier, 2)
            },
            'bonuses': {
                'word_length': len(word),
                'response_time': round(response_time, 2),
                'consecutive_success': consecutive_success,
                'is_fast': response_time <= self.SPEED_BONUS_THRESHOLD,
                'is_combo': consecutive_success >= self.COMBO_THRESHOLD,
                'is_rare': len(word) >= 5,
                'is_special': special_multiplier > 1.0
            }
        }
    
    def _calculate_rarity_multiplier(self, word: str) -> float:
        """희귀도 배수 계산 (글자 수 기반)"""
        word_length = len(word)
        
        # 8글자 이상은 최고 희귀도
        if word_length >= 8:
            return self.RARITY_SCORES[8]
        
        return self.RARITY_SCORES.get(word_length, 1.0)
    
    def _calculate_speed_multiplier(self, response_time: float) -> float:
        """속도 보너스 계산"""
        if response_time <= 0:
            return 1.0
        
        if response_time <= self.SPEED_BONUS_THRESHOLD:
            # 지수적 감소 함수 사용
            # 1초 = 2배, 3초 = 1.5배, 5초 = 1.0배
            multiplier = 1.0 + (self.MAX_SPEED_BONUS - 1.0) * math.exp(
                -response_time / 2.0
            )
            return min(multiplier, self.MAX_SPEED_BONUS)
        
        return 1.0
    
    def _calculate_combo_multiplier(self, consecutive_success: int) -> float:
        """콤보 배수 계산"""
        if consecutive_success < self.COMBO_THRESHOLD:
            return 1.0
        
        # 로그 함수를 사용한 점진적 증가
        # 3연속 = 1.2배, 5연속 = 1.5배, 10연속 = 2.0배, 20연속 = 3.0배
        combo_bonus = 1.0 + math.log(consecutive_success) * 0.3
        return min(combo_bonus, self.MAX_COMBO_MULTIPLIER)
    
    def _calculate_special_word_multiplier(self, word: str) -> float:
        """특수 단어 보너스 계산"""
        # 한국어 특수 패턴 체크
        multiplier = 1.0
        
        # 복합어 체크 (7글자 이상 복잡한 단어)
        if len(word) >= 7 and self._is_complex_word(word):
            multiplier *= 1.3
        
        # 고급 어휘 체크
        if self._is_advanced_vocabulary(word):
            multiplier *= 1.5
        
        # 한자어 체크
        if self._is_sino_korean_word(word):
            multiplier *= 1.2
        
        return multiplier
    
    def _is_complex_word(self, word: str) -> bool:
        """복합어 여부 판단"""
        # 간단한 휴리스틱: 7글자 이상이면서 반복되는 글자가 적은 경우
        if len(word) < 7:
            return False
        
        unique_chars = len(set(word))
        return unique_chars / len(word) > 0.7  # 70% 이상이 서로 다른 글자
    
    def _is_advanced_vocabulary(self, word: str) -> bool:
        """고급 어휘 여부 판단"""
        # 고급 어휘 패턴들
        advanced_patterns = [
            '철학', '경제', '정치', '과학', '기술', '예술', '문화',
            '사회', '역사', '지리', '수학', '물리', '화학', '생물'
        ]
        
        return any(pattern in word for pattern in advanced_patterns)
    
    def _is_sino_korean_word(self, word: str) -> bool:
        """한자어 여부 판단 (간단한 휴리스틱)"""
        # 일반적인 한자어 패턴들
        sino_patterns = [
            '학교', '회사', '정부', '국가', '사회', '경제', '정치',
            '기술', '과학', '문화', '예술', '역사', '지리'
        ]
        
        return any(pattern in word for pattern in sino_patterns)
    
    def calculate_game_performance_bonus(
        self, 
        player_stats: Dict, 
        game_stats: Dict
    ) -> Dict[str, Any]:
        """게임 전체 성과 보너스 계산"""
        performance_bonus = {
            'total_bonus': 0,
            'achievements': []
        }
        
        # MVP 보너스 (최고 점수자)
        if player_stats.get('rank', 0) == 1:
            mvp_bonus = int(player_stats.get('score', 0) * 0.1)  # 10% 보너스
            performance_bonus['total_bonus'] += mvp_bonus
            performance_bonus['achievements'].append({
                'name': 'MVP',
                'description': '게임 최고 점수',
                'bonus': mvp_bonus
            })
        
        # 속도왕 보너스 (평균 응답시간 최단)
        avg_response = player_stats.get('average_response_time', float('inf'))
        if avg_response < 3.0 and player_stats.get('words_submitted', 0) >= 3:
            speed_bonus = 500
            performance_bonus['total_bonus'] += speed_bonus
            performance_bonus['achievements'].append({
                'name': '속도왕',
                'description': f'평균 응답시간 {avg_response:.1f}초',
                'bonus': speed_bonus
            })
        
        # 긴 단어 마스터 (5글자 이상 단어 많이 사용)
        longest_word = player_stats.get('longest_word', '')
        if len(longest_word) >= 7:
            length_bonus = len(longest_word) * 100
            performance_bonus['total_bonus'] += length_bonus
            performance_bonus['achievements'].append({
                'name': '긴 단어 마스터',
                'description': f'최장 단어: {longest_word} ({len(longest_word)}글자)',
                'bonus': length_bonus
            })
        
        # 일관성 보너스 (모든 단어를 시간 내에 제출)
        words_submitted = player_stats.get('words_submitted', 0)
        if words_submitted >= 5:  # 최소 5단어 이상 제출
            consistency_bonus = words_submitted * 50
            performance_bonus['total_bonus'] += consistency_bonus
            performance_bonus['achievements'].append({
                'name': '일관성 보너스',
                'description': f'{words_submitted}개 단어 모두 시간 내 제출',
                'bonus': consistency_bonus
            })
        
        return performance_bonus
    
    def create_score_breakdown_message(self, score_info: Dict) -> str:
        """점수 상세 정보 메시지 생성"""
        breakdown = score_info['breakdown']
        bonuses = score_info['bonuses']
        
        message_parts = [
            f"📊 점수 상세: {score_info['base_score']} → {score_info['final_score']}점"
        ]
        
        # 보너스 정보 추가
        if bonuses['is_fast']:
            message_parts.append(f"⚡ 빠른 응답 보너스 (×{breakdown['speed_multiplier']})")
        
        if bonuses['is_combo']:
            message_parts.append(f"🔥 {bonuses['consecutive_success']}연속 콤보 (×{breakdown['combo_multiplier']})")
        
        if bonuses['is_rare']:
            message_parts.append(f"💎 긴 단어 보너스 (×{breakdown['rarity_multiplier']})")
        
        if bonuses['is_special']:
            message_parts.append(f"🌟 특수 단어 보너스 (×{breakdown['special_multiplier']})")
        
        return "\n".join(message_parts)


# 전역 인스턴스
_score_calculator = AdvancedScoreCalculator()

def get_score_calculator() -> AdvancedScoreCalculator:
    """점수 계산기 인스턴스 반환"""
    return _score_calculator