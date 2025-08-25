"""
두음법칙 (Korean Dueum Rules) 테스트 케이스
"""

import pytest
from utils.dueum_rules import (
    dueum_rules, 
    get_dueum_alternatives, 
    check_dueum_word_validity, 
    get_dueum_display_text, 
    get_dueum_input_help,
    is_dueum_pair,
    generate_dueum_variants
)


class TestDueumRules:
    """두음법칙 기본 기능 테스트"""
    
    def test_get_dueum_alternatives_basic(self):
        """기본 두음법칙 대안 글자 테스트"""
        # ㄴ으로 시작하는 글자들 (원래 ㄹ)
        assert '라' in get_dueum_alternatives('나')
        assert '락' in get_dueum_alternatives('낙')
        assert '란' in get_dueum_alternatives('난')
        assert '람' in get_dueum_alternatives('남')
        
        # ㅇ으로 시작하는 글자들 (원래 ㄹ/ㄴ)
        assert '료' in get_dueum_alternatives('요')
        assert '료' in get_dueum_alternatives('요') or '뇨' in get_dueum_alternatives('요')
        assert '류' in get_dueum_alternatives('유')
        assert '력' in get_dueum_alternatives('역')
        assert '련' in get_dueum_alternatives('연')
        
        # 두음법칙이 적용되지 않는 글자
        assert get_dueum_alternatives('가') == []
        assert get_dueum_alternatives('바') == []
        assert get_dueum_alternatives('사') == []
        
    def test_get_dueum_alternatives_reverse(self):
        """역방향 두음법칙 대안 글자 테스트"""
        # ㄹ로 시작하는 글자들
        assert '나' in get_dueum_alternatives('라')
        assert '낙' in get_dueum_alternatives('락')
        assert '난' in get_dueum_alternatives('란')
        
        # 복수 대안이 있는 경우 (백엔드 구현에 따라 조정)
        alternatives = get_dueum_alternatives('려')
        assert '여' in alternatives
        # '녀'는 구현에 따라 포함될 수 있음
        
    def test_is_dueum_applicable(self):
        """두음법칙 적용 대상 확인"""
        assert dueum_rules.is_dueum_applicable('요리')
        assert dueum_rules.is_dueum_applicable('나라')
        assert dueum_rules.is_dueum_applicable('역사')
        assert dueum_rules.is_dueum_applicable('연구')
        
        assert not dueum_rules.is_dueum_applicable('가방')
        assert not dueum_rules.is_dueum_applicable('책상')
        assert not dueum_rules.is_dueum_applicable('컴퓨터')
        
    def test_generate_dueum_variants(self):
        """두음법칙 변형 생성 테스트"""
        variants = generate_dueum_variants('요리')
        assert '료리' in variants
        assert '뇨리' in variants
        
        variants = generate_dueum_variants('나라')
        assert '라라' in variants  # 실제로는 '라라'는 이상하지만 알고리즘적으로는 맞음
        
        variants = generate_dueum_variants('역사')
        assert '력사' in variants
        assert '녁사' in variants
        
        # 두음법칙이 없는 단어
        variants = generate_dueum_variants('가방')
        assert variants == []


class TestDueumWordValidity:
    """두음법칙 단어 유효성 검증 테스트"""
    
    def test_direct_match(self):
        """직접 일치하는 경우"""
        is_valid, valid_chars = check_dueum_word_validity('가방', '가')
        assert is_valid
        assert '가' in valid_chars
        
    def test_dueum_match_basic(self):
        """기본 두음법칙 일치"""
        # 요리 (료리, 뇨리로도 가능)
        is_valid, valid_chars = check_dueum_word_validity('요리', '료')
        assert is_valid
        assert len(valid_chars) >= 2
        
        is_valid, valid_chars = check_dueum_word_validity('요리', '뇨')
        assert is_valid
        
        # 나라 (라라로도 가능)
        is_valid, valid_chars = check_dueum_word_validity('나라', '라')
        assert is_valid
        
        is_valid, valid_chars = check_dueum_word_validity('라라', '나')
        assert is_valid
        
    def test_dueum_match_complex(self):
        """복합 두음법칙 일치"""
        # 역사 (력사, 녁사로도 가능)
        is_valid, valid_chars = check_dueum_word_validity('역사', '력')
        assert is_valid
        
        is_valid, valid_chars = check_dueum_word_validity('역사', '녁')
        assert is_valid
        
        # 연구 (련구, 년구로도 가능)
        is_valid, valid_chars = check_dueum_word_validity('연구', '련')
        assert is_valid
        
        is_valid, valid_chars = check_dueum_word_validity('연구', '년')
        assert is_valid
        
    def test_dueum_mismatch(self):
        """두음법칙 불일치"""
        is_valid, valid_chars = check_dueum_word_validity('가방', '나')
        assert not is_valid
        assert len(valid_chars) == 0
        
        is_valid, valid_chars = check_dueum_word_validity('책상', '요')
        assert not is_valid
        
    def test_empty_inputs(self):
        """빈 입력값 처리"""
        is_valid, valid_chars = check_dueum_word_validity('', '가')
        assert not is_valid
        
        is_valid, valid_chars = check_dueum_word_validity('가방', '')
        assert not is_valid


class TestDueumDisplay:
    """두음법칙 표시 관련 테스트"""
    
    def test_display_text(self):
        """UI 표시 텍스트"""
        # 두음법칙이 있는 글자
        display = get_dueum_display_text('요')
        assert '료' in display or '뇨' in display
        assert '요' in display
        
        display = get_dueum_display_text('나')
        assert '라' in display
        assert '나' in display
        
        # 두음법칙이 없는 글자
        display = get_dueum_display_text('가')
        assert display == '가'
        
    def test_input_help_text(self):
        """입력 도움말 텍스트"""
        help_text = get_dueum_input_help('요')
        assert '요' in help_text
        assert '단어' in help_text
        assert '료' in help_text or '뇨' in help_text
        
        help_text = get_dueum_input_help('가')
        assert '가' in help_text
        assert '단어' in help_text
        
    def test_is_dueum_pair(self):
        """두음법칙 쌍 확인"""
        assert is_dueum_pair('요', '료')
        assert is_dueum_pair('요', '뇨')
        assert is_dueum_pair('나', '라')
        assert is_dueum_pair('역', '력')
        assert is_dueum_pair('역', '녁')
        
        # 같은 글자
        assert is_dueum_pair('가', '가')
        
        # 관계없는 글자
        assert not is_dueum_pair('가', '나')
        assert not is_dueum_pair('바', '사')


class TestDueumExamples:
    """두음법칙 실제 단어 예시 테스트"""
    
    def test_common_dueum_words(self):
        """일반적인 두음법칙 단어들"""
        test_cases = [
            ('요리', ['료', '뇨']),
            ('여행', ['려', '녀']),
            ('역사', ['력', '녁']),
            ('연구', ['련', '년']),
            ('영화', ['령', '녕']),
            ('용기', ['룡']),
            ('유학', ['류', '뉴']),
            ('음식', ['름']),
            ('이론', ['리', '니']),
            ('인간', ['린']),
            ('나이', ['라']),
            ('남자', ['람']),
            ('농업', ['롱']),
            ('누나', ['루']),
            ('능력', ['릉']),
        ]
        
        for word, target_chars in test_cases:
            for target_char in target_chars:
                is_valid, _ = check_dueum_word_validity(word, target_char)
                assert is_valid, f"'{word}'이(가) '{target_char}'로 시작하는 것으로 인정되지 않음"
                
    def test_edge_cases(self):
        """경계 사례 테스트"""
        # 단일 글자
        is_valid, _ = check_dueum_word_validity('나', '라')
        assert is_valid
        
        # 매우 긴 단어
        long_word = '나' + '가' * 50
        is_valid, _ = check_dueum_word_validity(long_word, '라')
        assert is_valid
        
    def test_normalize_for_comparison(self):
        """비교용 정규화 테스트"""
        normalized = dueum_rules.normalize_for_comparison('요리')
        assert '요리' in normalized
        assert '료리' in normalized
        assert '뇨리' in normalized
        
        # 두음법칙이 없는 단어
        normalized = dueum_rules.normalize_for_comparison('가방')
        assert normalized == ['가방']
        
    def test_get_all_possible_starts(self):
        """가능한 시작 글자 모음 테스트"""
        possible = dueum_rules.get_all_possible_starts('요')
        assert '요' in possible
        assert '료' in possible
        assert '뇨' in possible
        
        possible = dueum_rules.get_all_possible_starts('가')
        assert possible == {'가'}


class TestDueumIntegration:
    """두음법칙 통합 테스트"""
    
    def test_full_workflow(self):
        """전체 워크플로우 테스트"""
        target_char = '요'
        input_word = '요리'
        
        # 1. 대안 글자들 확인
        alternatives = get_dueum_alternatives(target_char)
        assert len(alternatives) > 0
        
        # 2. 단어 유효성 검사
        is_valid, valid_chars = check_dueum_word_validity(input_word, target_char)
        assert is_valid
        
        # 3. 표시 텍스트 생성
        display_text = get_dueum_display_text(target_char)
        assert target_char in display_text
        
        # 4. 도움말 텍스트 생성
        help_text = get_dueum_input_help(target_char)
        assert target_char in help_text
        
    def test_performance(self):
        """성능 테스트 (기본적인)"""
        import time
        
        # 대량의 두음법칙 검사
        start_time = time.time()
        
        test_words = ['요리', '여행', '역사', '연구', '영화', '나라', '남자', '농업'] * 100
        test_chars = ['요', '여', '역', '연', '영', '나', '남', '농'] * 100
        
        for word, char in zip(test_words, test_chars):
            check_dueum_word_validity(word, char)
            
        end_time = time.time()
        
        # 800번의 검증이 1초 내에 완료되어야 함
        assert (end_time - start_time) < 1.0
        
    def test_memory_usage(self):
        """메모리 사용량 테스트"""
        import sys
        
        # 두음법칙 인스턴스가 합리적인 크기인지 확인
        dueum_size = sys.getsizeof(dueum_rules.dueum_mappings)
        reverse_size = sys.getsizeof(dueum_rules.reverse_mappings)
        
        # 매핑 테이블들이 과도하게 크지 않은지 확인 (예: 10KB 이하)
        assert dueum_size < 10240  # 10KB
        assert reverse_size < 10240  # 10KB


if __name__ == '__main__':
    pytest.main([__file__, '-v'])