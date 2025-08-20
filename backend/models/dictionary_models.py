from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .base import Base


class KoreanDictionary(Base):
    """한국어 사전 모델"""
    __tablename__ = "korean_dictionary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), unique=True, nullable=False, index=True)
    definition = Column(Text)
    difficulty_level = Column(Integer, default=1, index=True)  # 1: 쉬움, 2: 보통, 3: 어려움
    frequency_score = Column(Integer, default=0)  # 사용 빈도
    word_type = Column(String(20))  # 명사, 동사, 형용사 등
    first_char = Column(String(1), nullable=False, index=True)
    last_char = Column(String(1), nullable=False, index=True)
    word_length = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<KoreanDictionary(word='{self.word}', difficulty={self.difficulty_level})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "word": self.word,
            "definition": self.definition,
            "difficulty_level": self.difficulty_level,
            "frequency_score": self.frequency_score,
            "word_type": self.word_type,
            "first_char": self.first_char,
            "last_char": self.last_char,
            "word_length": self.word_length,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_difficulty_multiplier(cls, difficulty_level: int) -> float:
        """난이도별 점수 배수 반환"""
        multipliers = {1: 1.0, 2: 1.5, 3: 2.0}
        return multipliers.get(difficulty_level, 1.0)
    
    @classmethod
    def get_frequency_bonus(cls, frequency_score: int) -> int:
        """빈도별 보너스 점수 반환"""
        if frequency_score >= 90:
            return 10
        elif frequency_score >= 70:
            return 20
        elif frequency_score >= 50:
            return 30
        else:
            return 50  # 희귀한 단어일수록 높은 보너스