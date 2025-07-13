from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from db.postgres import Base

class PlayerGameStats(Base):
    """플레이어 게임 통계 모델 - 게임 종료 후 플레이어별 통계를 저장"""
    __tablename__ = "player_game_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_log_id = Column(Integer, ForeignKey("game_logs.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    
    # 기본 통계
    words_submitted = Column(Integer, nullable=False, default=0)
    valid_words = Column(Integer, nullable=False, default=0)
    invalid_words = Column(Integer, nullable=False, default=0)
    
    # 점수 정보
    total_score = Column(Integer, nullable=False, default=0)
    word_score = Column(Integer, nullable=False, default=0)  # 단어 자체 점수
    bonus_score = Column(Integer, nullable=False, default=0)  # 보너스 점수
    
    # 시간 통계
    total_response_time = Column(Float, nullable=False, default=0.0)
    avg_response_time = Column(Float, nullable=True)
    fastest_response_time = Column(Float, nullable=True)
    slowest_response_time = Column(Float, nullable=True)
    
    # 단어 통계
    longest_word = Column(String(100), nullable=True)
    longest_word_length = Column(Integer, nullable=False, default=0)
    shortest_word = Column(String(100), nullable=True)
    shortest_word_length = Column(Integer, nullable=True)
    
    # 게임 결과
    rank = Column(Integer, nullable=False, default=0)  # 순위 (1위, 2위, ...)
    is_winner = Column(Integer, nullable=False, default=0)  # 1: 승자, 0: 패자
    
    # 추가 통계
    time_violations = Column(Integer, nullable=False, default=0)  # 시간 초과 횟수
    consecutive_words = Column(Integer, nullable=False, default=0)  # 최대 연속 성공 단어 수
    
    # 생성 시간
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정 (순환 import 문제로 주석 처리)
    # game_log = relationship("GameLog", back_populates="player_game_stats")
    # player = relationship("Guest")
    
    def __repr__(self):
        return f"<PlayerGameStats(id={self.id}, player_id={self.player_id}, rank={self.rank}, total_score={self.total_score})>"

    def calculate_average_response_time(self):
        """평균 응답 시간을 계산합니다"""
        if self.words_submitted > 0 and self.total_response_time > 0:
            self.avg_response_time = round(self.total_response_time / self.words_submitted, 2)
        else:
            self.avg_response_time = 0.0
        return self.avg_response_time

    def update_word_stats(self, word: str, response_time: float, score: int):
        """단어 통계를 업데이트합니다"""
        # 단어 수 증가
        self.words_submitted += 1
        self.valid_words += 1
        
        # 점수 업데이트
        self.total_score += score
        
        # 응답 시간 업데이트
        self.total_response_time += response_time
        
        # 최단/최장 응답 시간 업데이트
        if self.fastest_response_time is None or response_time < self.fastest_response_time:
            self.fastest_response_time = response_time
        if self.slowest_response_time is None or response_time > self.slowest_response_time:
            self.slowest_response_time = response_time
            
        # 최장/최단 단어 업데이트
        word_length = len(word)
        if self.longest_word_length < word_length:
            self.longest_word = word
            self.longest_word_length = word_length
        if self.shortest_word_length is None or word_length < self.shortest_word_length:
            self.shortest_word = word
            self.shortest_word_length = word_length
            
        # 평균 응답 시간 재계산
        self.calculate_average_response_time()

    def add_invalid_word(self):
        """무효한 단어 제출 시 통계 업데이트"""
        self.words_submitted += 1
        self.invalid_words += 1

    def add_time_violation(self):
        """시간 초과 발생 시 통계 업데이트"""
        self.time_violations += 1

    def get_success_rate(self):
        """성공률을 계산합니다 (유효한 단어 / 전체 제출 단어)"""
        if self.words_submitted == 0:
            return 0.0
        return round((self.valid_words / self.words_submitted) * 100, 1)