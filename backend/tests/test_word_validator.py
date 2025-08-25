import pytest
from services.word_validator import WordValidator

class TestWordValidator:
    def setup_method(self):
        self.validator = WordValidator()
    
    def test_is_valid_korean_word(self):
        """한글 단어 유효성 검사"""
        assert self.validator.is_valid_korean_word("사과") == True
        assert self.validator.is_valid_korean_word("apple") == False
        assert self.validator.is_valid_korean_word("123") == False
        assert self.validator.is_valid_korean_word("사과123") == False
    
    def test_validate_word_chain(self):
        """끝말잇기 규칙 검증"""
        # 정상적인 끝말잇기
        is_valid, message = self.validator.validate_word_chain("사과", "과일")
        assert is_valid == True
        
        # 잘못된 끝말잇기
        is_valid, message = self.validator.validate_word_chain("사과", "바나나")
        assert is_valid == False
        assert "끝말이 이어지지 않습니다" in message
    
    def test_check_word_difficulty(self):
        """단어 난이도 계산"""
        # 2글자 단어
        difficulty = self.validator.check_word_difficulty("사과")
        assert difficulty == 1
        
        # 3글자 단어
        difficulty = self.validator.check_word_difficulty("바나나")
        assert difficulty == 2
        
        # 4글자 이상
        difficulty = self.validator.check_word_difficulty("아메리카노")
        assert difficulty == 3