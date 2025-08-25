"""
Korean Dueum Rules (두음법칙) Utility Module

This module handles Korean initial sound change rules where certain consonants
at the beginning of words are replaced with other consonants in modern Korean.

Key Rules:
1. ㄹ → ㄴ: 라면 → 나면 (but 나면 is not used, 라면 stays)
2. ㄹ → ㅇ: 료리 → 요리 (cooking)  
3. ㄴ → ㅇ: 뇨리 → 요리 (same word)
4. Initial ㄹ/ㄴ can become silent (ㅇ) in compound words
"""

from typing import Dict, List, Set, Tuple, Optional


class DueumRules:
    def __init__(self):
        # 두음법칙 매핑: 변환된 글자 → 원래 글자들
        self.dueum_mappings = {
            # ㄴ으로 시작 (원래 ㄹ)
            '나': ['라'], '낙': ['락'], '난': ['란'], '날': ['랄'], '남': ['람'],
            '납': ['랍'], '낭': ['랑'], '내': ['래'], '냉': ['랭'], '녹': ['록'],
            '논': ['론'], '농': ['롱'], '뇌': ['뢰'], '누': ['루'], '능': ['릉'],
            '님': ['림'], '닙': ['립'], '노': ['로'], '뇽': ['룡'],
            
            # ㅇ으로 시작 (원래 ㄹ/ㄴ)
            '약': ['략'], '양': ['량'], '여': ['려', '녀'], '역': ['력', '녁'], 
            '연': ['련', '년'], '열': ['렬'], '염': ['렴', '념'], '엽': ['렵', '녑'], 
            '영': ['령', '녕'], '예': ['례'], '요': ['료', '뇨'], '용': ['룡'], 
            '유': ['류', '뉴'], '육': ['륙', '뉵'], '윤': ['륜'], '율': ['률'], 
            '융': ['륭'], '음': ['름'], '이': ['리', '니'], '인': ['린'], 
            '임': ['림'], '입': ['립'], '일': ['릴'], '익': ['릭'],
            
            # 추가 두음법칙 패턴
            '아': ['라'], '안': ['란'], '알': ['랄'], '암': ['람'], '압': ['랍'],
            '앙': ['랑'], '애': ['래'], '액': ['랙'], '앤': ['랜'], '앨': ['랠'],
            '앰': ['램'], '앱': ['랩'], '앵': ['랭'], '어': ['러'], '억': ['럭'],
            '언': ['런'], '얼': ['럴'], '엄': ['럼'], '업': ['럽'], '엉': ['렁'],
            '에': ['레'], '엑': ['렉'], '엔': ['렌'], '엘': ['렐'], '엠': ['렘'],
            '엡': ['렙'], '엥': ['렝'], '오': ['로'], '옥': ['록'], '온': ['론'],
            '올': ['롤'], '옴': ['롬'], '옵': ['롭'], '옹': ['롱'], '우': ['루'],
            '욱': ['룩'], '운': ['룬'], '울': ['룰'], '움': ['룸'], '웁': ['룹'],
            '웅': ['룽'], '워': ['뤄'], '원': ['뤈'], '월': ['뤌'], '위': ['뤼'],
            '은': ['른'], '을': ['를'], '읍': ['릅'],
        }
        
        # 역방향 매핑: 원래 글자 → 변환된 글자
        self.reverse_mappings = {}
        for converted, originals in self.dueum_mappings.items():
            for original in originals:
                if original not in self.reverse_mappings:
                    self.reverse_mappings[original] = []
                self.reverse_mappings[original].append(converted)
        
        # 두음법칙이 적용되는 초성들
        self.dueum_initials = {'ㄹ', 'ㄴ'}
        
        # 두음법칙 단어 예시
        self.dueum_examples = {
            '요리': ['료리', '뇨리'],
            '여행': ['려행', '녀행'],
            '역사': ['력사', '녁사'],
            '연구': ['련구', '년구'],
            '열정': ['렬정'],
            '영화': ['령화', '녕화'],
            '용기': ['룡기'],
            '유학': ['류학', '뉴학'],
            '음식': ['름식'],
            '이론': ['리론', '니론'],
            '인간': ['린간'],
            '나이': ['라이'],
            '남자': ['람자'],
            '농업': ['롱업'],
            '누나': ['루나'],
            '능력': ['릉력'],
        }

    def get_dueum_alternatives(self, char: str) -> List[str]:
        """
        주어진 글자의 두음법칙 대안들을 반환
        
        Args:
            char: 검사할 한글 글자
            
        Returns:
            두음법칙 대안 글자들의 리스트
        """
        alternatives = []
        
        # 변환된 글자 → 원래 글자들
        if char in self.dueum_mappings:
            alternatives.extend(self.dueum_mappings[char])
            
        # 원래 글자 → 변환된 글자들  
        if char in self.reverse_mappings:
            alternatives.extend(self.reverse_mappings[char])
            
        return list(set(alternatives))
    
    def is_dueum_applicable(self, word: str) -> bool:
        """
        단어가 두음법칙 적용 대상인지 확인
        
        Args:
            word: 검사할 단어
            
        Returns:
            두음법칙 적용 가능 여부
        """
        if not word or len(word) < 1:
            return False
            
        first_char = word[0]
        return first_char in self.dueum_mappings or first_char in self.reverse_mappings
    
    def generate_dueum_variants(self, word: str) -> List[str]:
        """
        단어의 두음법칙 변형들을 생성
        
        Args:
            word: 원본 단어
            
        Returns:
            가능한 두음법칙 변형들의 리스트
        """
        if not word:
            return []
            
        variants = []
        first_char = word[0]
        rest_of_word = word[1:]
        
        alternatives = self.get_dueum_alternatives(first_char)
        for alt_char in alternatives:
            variant = alt_char + rest_of_word
            variants.append(variant)
            
        return variants
    
    def check_dueum_word_validity(self, input_word: str, target_char: str) -> Tuple[bool, List[str]]:
        """
        입력된 단어가 목표 글자로 시작하는지 두음법칙을 고려하여 검사
        
        Args:
            input_word: 사용자가 입력한 단어
            target_char: 목표 시작 글자
            
        Returns:
            (유효성, 가능한 대안 글자들)
        """
        if not input_word or not target_char:
            return False, []
            
        first_char = input_word[0]
        
        # 직접 일치
        if first_char == target_char:
            return True, [target_char]
            
        # 두음법칙 검사
        target_alternatives = self.get_dueum_alternatives(target_char)
        input_alternatives = self.get_dueum_alternatives(first_char)
        
        # 목표 글자의 대안 중에 입력 글자가 있는지
        if first_char in target_alternatives:
            return True, [target_char, first_char]
            
        # 입력 글자의 대안 중에 목표 글자가 있는지
        if target_char in input_alternatives:
            return True, [target_char, first_char]
            
        # 서로의 대안들이 겹치는지
        common_alternatives = set(target_alternatives) & set(input_alternatives)
        if common_alternatives:
            return True, [target_char, first_char] + list(common_alternatives)
            
        return False, []
    
    def get_display_text(self, char: str) -> str:
        """
        UI 표시용 두음법칙 텍스트 생성
        
        Args:
            char: 표시할 글자
            
        Returns:
            두음법칙 정보가 포함된 표시 텍스트
        """
        alternatives = self.get_dueum_alternatives(char)
        if alternatives:
            main_alt = alternatives[0]  # 주요 대안
            return f"{char}({main_alt})"
        return char
    
    def get_input_help_text(self, char: str) -> str:
        """
        입력 도움말 텍스트 생성
        
        Args:
            char: 목표 글자
            
        Returns:
            입력 가이드 텍스트
        """
        alternatives = self.get_dueum_alternatives(char)
        if alternatives:
            alt_text = "/".join(alternatives[:2])  # 최대 2개 대안만 표시
            return f"{char}({alt_text})로 시작하는 단어"
        return f"{char}로 시작하는 단어"
    
    def is_dueum_pair(self, char1: str, char2: str) -> bool:
        """
        두 글자가 두음법칙 관계인지 확인
        
        Args:
            char1: 첫 번째 글자
            char2: 두 번째 글자
            
        Returns:
            두음법칙 관계 여부
        """
        if char1 == char2:
            return True
            
        alternatives1 = self.get_dueum_alternatives(char1)
        alternatives2 = self.get_dueum_alternatives(char2)
        
        return char2 in alternatives1 or char1 in alternatives2
    
    def normalize_for_comparison(self, word: str) -> List[str]:
        """
        비교를 위해 단어를 정규화 (모든 두음법칙 변형 포함)
        
        Args:
            word: 정규화할 단어
            
        Returns:
            정규화된 단어들의 리스트
        """
        if not word:
            return []
            
        normalized = [word]  # 원본 포함
        variants = self.generate_dueum_variants(word)
        normalized.extend(variants)
        
        return list(set(normalized))
    
    def get_all_possible_starts(self, char: str) -> Set[str]:
        """
        특정 글자로 시작할 수 있는 모든 두음법칙 글자들 반환
        
        Args:
            char: 기준 글자
            
        Returns:
            가능한 시작 글자들의 집합
        """
        possible_starts = {char}
        alternatives = self.get_dueum_alternatives(char)
        possible_starts.update(alternatives)
        return possible_starts


# 전역 인스턴스
dueum_rules = DueumRules()

# 편의 함수들
def get_dueum_alternatives(char: str) -> List[str]:
    """두음법칙 대안 글자들 반환"""
    return dueum_rules.get_dueum_alternatives(char)

def check_dueum_word_validity(input_word: str, target_char: str) -> Tuple[bool, List[str]]:
    """두음법칙을 고려한 단어 유효성 검사"""
    return dueum_rules.check_dueum_word_validity(input_word, target_char)

def get_dueum_display_text(char: str) -> str:
    """UI 표시용 두음법칙 텍스트"""
    return dueum_rules.get_display_text(char)

def get_dueum_input_help(char: str) -> str:
    """입력 도움말 텍스트"""
    return dueum_rules.get_input_help_text(char)

def is_dueum_pair(char1: str, char2: str) -> bool:
    """두 글자가 두음법칙 관계인지 확인"""
    return dueum_rules.is_dueum_pair(char1, char2)

def generate_dueum_variants(word: str) -> List[str]:
    """단어의 두음법칙 변형들 생성"""
    return dueum_rules.generate_dueum_variants(word)