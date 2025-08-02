"""
고급 점수 계산 서비스 테스트
"""

import pytest
from services.advanced_score_service import AdvancedScoreCalculator


@pytest.fixture
def score_calculator():
    """고급 점수 계산기 인스턴스"""
    return AdvancedScoreCalculator()


class TestAdvancedScoreCalculator:
    """고급 점수 계산기 테스트"""
    
    def test_basic_word_score_calculation(self, score_calculator):
        """기본 단어 점수 계산 테스트"""
        # 3글자 단어, 일반 응답 시간
        score = score_calculator.calculate_word_score(
            word="사과",
            response_time=10.0,
            consecutive_success=0
        )
        
        # 기본 점수: 2글자 * 10 = 20
        # 글자 수 보너스: 1.0배 (2글자)
        # 속도 보너스: 1.0배 (10초는 느림)
        # 콤보 보너스: 1.0배 (연속 성공 없음)
        expected_score = 20 * 1.0 * 1.0 * 1.0
        assert score == expected_score
    
    def test_speed_bonus_calculation(self, score_calculator):
        """속도 보너스 계산 테스트"""
        # 매우 빠른 응답 (2초)
        fast_score = score_calculator.calculate_word_score(
            word="빠름",
            response_time=2.0,
            consecutive_success=0
        )
        
        # 느린 응답 (10초)
        slow_score = score_calculator.calculate_word_score(
            word="느림",
            response_time=10.0,
            consecutive_success=0
        )
        
        # 빠른 응답이 더 높은 점수를 받아야 함
        assert fast_score > slow_score
    
    def test_word_length_rarity_bonus(self, score_calculator):
        """단어 길이에 따른 희귀도 보너스 테스트"""
        # 2글자 단어
        short_score = score_calculator.calculate_word_score(
            word="가나",
            response_time=5.0,
            consecutive_success=0
        )
        
        # 5글자 단어
        long_score = score_calculator.calculate_word_score(
            word="프로그래밍",
            response_time=5.0,
            consecutive_success=0
        )
        
        # 긴 단어가 더 높은 점수를 받아야 함
        assert long_score > short_score
    
    def test_combo_multiplier(self, score_calculator):
        """콤보 배수 계산 테스트"""
        base_word = "테스트"
        base_time = 5.0
        
        # 콤보 없음
        no_combo_score = score_calculator.calculate_word_score(
            word=base_word,
            response_time=base_time,
            consecutive_success=0
        )
        
        # 3연속 성공 (콤보 시작)
        combo3_score = score_calculator.calculate_word_score(
            word=base_word,
            response_time=base_time,
            consecutive_success=3
        )
        
        # 10연속 성공 (높은 콤보)
        combo10_score = score_calculator.calculate_word_score(
            word=base_word,
            response_time=base_time,
            consecutive_success=10
        )
        
        # 콤보가 높을수록 점수가 높아야 함
        assert combo3_score > no_combo_score
        assert combo10_score > combo3_score
    
    def test_maximum_speed_bonus(self, score_calculator):
        """최대 속도 보너스 테스트"""
        # 매우 빠른 응답 (1초)
        very_fast_score = score_calculator.calculate_word_score(
            word="초고속",
            response_time=1.0,
            consecutive_success=0
        )
        
        # 극도로 빠른 응답 (0.5초)
        ultra_fast_score = score_calculator.calculate_word_score(
            word="초고속",
            response_time=0.5,
            consecutive_success=0
        )
        
        # 최대 속도 보너스 제한 확인
        # 둘 다 최대 보너스를 받아야 하므로 점수가 같아야 함
        assert very_fast_score == ultra_fast_score
    
    def test_maximum_combo_multiplier(self, score_calculator):
        """최대 콤보 배수 테스트"""
        base_word = "최대콤보"
        base_time = 5.0
        
        # 매우 높은 콤보 (50연속)
        high_combo_score = score_calculator.calculate_word_score(
            word=base_word,
            response_time=base_time,
            consecutive_success=50
        )
        
        # 극도로 높은 콤보 (100연속)
        ultra_combo_score = score_calculator.calculate_word_score(
            word=base_word,
            response_time=base_time,
            consecutive_success=100
        )
        
        # 최대 콤보 배수 제한 확인
        # 최대값에 도달하면 더 이상 증가하지 않아야 함
        assert high_combo_score == ultra_combo_score
    
    def test_very_long_word_rarity(self, score_calculator):
        """매우 긴 단어의 희귀도 보너스 테스트"""
        # 8글자 이상의 단어는 최대 희귀도 보너스를 받아야 함
        word_8chars = "가나다라마바사아"  # 8글자
        word_10chars = "가나다라마바사아자차"  # 10글자
        
        score_8 = score_calculator.calculate_word_score(
            word=word_8chars,
            response_time=5.0,
            consecutive_success=0
        )
        
        score_10 = score_calculator.calculate_word_score(
            word=word_10chars,
            response_time=5.0,
            consecutive_success=0
        )
        
        # 8글자 이상은 모두 최대 희귀도 보너스를 받으므로
        # 기본 점수의 차이만 있어야 함
        expected_ratio = len(word_10chars) / len(word_8chars)
        actual_ratio = score_10 / score_8
        assert abs(actual_ratio - expected_ratio) < 0.01
    
    def test_combined_bonuses(self, score_calculator):
        """모든 보너스가 결합된 경우 테스트"""
        # 완벽한 조건: 긴 단어 + 빠른 응답 + 높은 콤보
        perfect_score = score_calculator.calculate_word_score(
            word="프로그래밍언어",  # 7글자
            response_time=2.0,     # 빠른 응답
            consecutive_success=10  # 높은 콤보
        )
        
        # 일반적인 조건
        normal_score = score_calculator.calculate_word_score(
            word="단어",            # 2글자
            response_time=8.0,     # 보통 응답
            consecutive_success=0   # 콤보 없음
        )
        
        # 완벽한 조건이 훨씬 높은 점수를 받아야 함
        assert perfect_score > normal_score * 5  # 최소 5배 이상
    
    def test_get_speed_multiplier(self, score_calculator):
        """속도 배수 계산 메서드 테스트"""
        # 매우 빠른 응답
        fast_multiplier = score_calculator.get_speed_multiplier(1.0)
        assert fast_multiplier == score_calculator.MAX_SPEED_BONUS
        
        # 보통 속도
        normal_multiplier = score_calculator.get_speed_multiplier(5.0)
        assert normal_multiplier == 1.0
        
        # 느린 응답
        slow_multiplier = score_calculator.get_speed_multiplier(10.0)
        assert slow_multiplier == 1.0
    
    def test_get_rarity_multiplier(self, score_calculator):
        """희귀도 배수 계산 메서드 테스트"""
        # 다양한 길이의 단어들
        assert score_calculator.get_rarity_multiplier("가나") == 1.0      # 2글자
        assert score_calculator.get_rarity_multiplier("가나다") == 1.2    # 3글자
        assert score_calculator.get_rarity_multiplier("가나다라") == 1.5  # 4글자
        assert score_calculator.get_rarity_multiplier("가나다라마") == 2.0  # 5글자
        
        # 8글자 이상은 최대값
        long_word = "가나다라마바사아자차"
        assert score_calculator.get_rarity_multiplier(long_word) == 4.0
    
    def test_get_combo_multiplier(self, score_calculator):
        """콤보 배수 계산 메서드 테스트"""
        # 콤보 임계값 미만
        assert score_calculator.get_combo_multiplier(0) == 1.0
        assert score_calculator.get_combo_multiplier(2) == 1.0
        
        # 콤보 시작
        assert score_calculator.get_combo_multiplier(3) > 1.0
        
        # 높은 콤보
        high_combo_multiplier = score_calculator.get_combo_multiplier(20)
        assert high_combo_multiplier > score_calculator.get_combo_multiplier(3)
        assert high_combo_multiplier <= score_calculator.MAX_COMBO_MULTIPLIER
    
    def test_edge_cases(self, score_calculator):
        """엣지 케이스 테스트"""
        # 빈 문자열
        empty_score = score_calculator.calculate_word_score("", 5.0, 0)
        assert empty_score == 0
        
        # 1글자 단어
        single_char_score = score_calculator.calculate_word_score("가", 5.0, 0)
        assert single_char_score > 0
        
        # 음수 응답 시간 (비현실적이지만 처리되어야 함)
        negative_time_score = score_calculator.calculate_word_score("테스트", -1.0, 0)
        assert negative_time_score > 0  # 최대 보너스를 받아야 함
        
        # 음수 연속 성공 (비현실적이지만 처리되어야 함)
        negative_combo_score = score_calculator.calculate_word_score("테스트", 5.0, -1)
        assert negative_combo_score > 0  # 콤보 없음으로 처리되어야 함
    
    def test_score_consistency(self, score_calculator):
        """점수 계산 일관성 테스트"""
        word = "일관성테스트"
        response_time = 4.0
        consecutive_success = 5
        
        # 같은 조건으로 여러 번 계산해도 같은 결과가 나와야 함
        score1 = score_calculator.calculate_word_score(word, response_time, consecutive_success)
        score2 = score_calculator.calculate_word_score(word, response_time, consecutive_success)
        score3 = score_calculator.calculate_word_score(word, response_time, consecutive_success)
        
        assert score1 == score2 == score3
    
    def test_realistic_score_ranges(self, score_calculator):
        """현실적인 점수 범위 테스트"""
        # 일반적인 게임 시나리오들
        scenarios = [
            ("사과", 6.0, 0),        # 초보자의 일반적인 플레이
            ("컴퓨터", 4.0, 3),      # 중급자의 플레이
            ("프로그래밍", 2.5, 10), # 고급자의 플레이
        ]
        
        scores = []
        for word, time, combo in scenarios:
            score = score_calculator.calculate_word_score(word, time, combo)
            scores.append(score)
            # 점수가 합리적인 범위에 있는지 확인
            assert 10 <= score <= 1000  # 너무 낮거나 높지 않아야 함
        
        # 더 어려운 조건일수록 높은 점수
        assert scores[0] < scores[1] < scores[2]