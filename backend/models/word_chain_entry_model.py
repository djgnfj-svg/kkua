from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from db.postgres import Base

class WordChainEntry(Base):
    """단어 체인 엔트리 모델 - 게임 중 제출된 각 단어의 기록을 저장"""
    __tablename__ = "word_chain_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_log_id = Column(Integer, ForeignKey("game_logs.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    
    # 단어 정보
    word = Column(String(100), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False, default=1)
    
    # 시간 정보
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    response_time = Column(Float, nullable=True)  # 응답 시간 (초)
    
    # 단어 검증 정보
    is_valid = Column(Integer, nullable=False, default=1)  # 1: 유효, 0: 무효
    validation_message = Column(String(200), nullable=True)  # 검증 실패 사유
    
    # 점수 정보
    word_score = Column(Integer, nullable=False, default=0)  # 단어별 점수
    bonus_score = Column(Integer, nullable=False, default=0)  # 보너스 점수
    
    # 생성 시간
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계 설정 (순환 import 문제로 주석 처리)
    # game_log = relationship("GameLog", back_populates="word_chain_entries")
    # player = relationship("Guest")
    
    def __repr__(self):
        return f"<WordChainEntry(id={self.id}, word='{self.word}', player_id={self.player_id}, turn_number={self.turn_number})>"

    def calculate_word_score(self):
        """단어 점수를 계산합니다"""
        if not self.word:
            return 0
        
        # 기본 점수: 글자 수
        base_score = len(self.word)
        
        # 보너스 점수 계산
        bonus = 0
        
        # 긴 단어 보너스 (5글자 이상)
        if len(self.word) >= 5:
            bonus += 2
        if len(self.word) >= 7:
            bonus += 3
            
        # 빠른 응답 보너스 (3초 이내)
        if self.response_time and self.response_time <= 3.0:
            bonus += 1
            
        self.word_score = base_score
        self.bonus_score = bonus
        
        return base_score + bonus

    def get_total_score(self):
        """총 점수를 반환합니다"""
        return self.word_score + self.bonus_score