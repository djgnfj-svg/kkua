"""
분석 서비스
게임 통계, 사용자 행동 분석, 성과 지표, 리포팅
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from database import get_db, get_redis
from redis_models import GameState
from models.user_models import User
from models.game_models import GameSession
from sqlalchemy import select, func, and_, desc
import json

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """지표 타입"""
    COUNTER = "counter"                # 카운터 (증가만)
    GAUGE = "gauge"                    # 게이지 (증감 가능)
    HISTOGRAM = "histogram"            # 히스토그램
    SUMMARY = "summary"                # 요약 통계


class AnalyticsPeriod(str, Enum):
    """분석 기간"""
    REALTIME = "realtime"              # 실시간
    HOURLY = "hourly"                  # 시간별
    DAILY = "daily"                    # 일별
    WEEKLY = "weekly"                  # 주별
    MONTHLY = "monthly"                # 월별


@dataclass
class GameMetrics:
    """게임 지표"""
    total_games: int = 0
    active_games: int = 0
    total_players: int = 0
    active_players: int = 0
    average_game_duration: float = 0.0
    average_words_per_game: float = 0.0
    top_scores: List[int] = None
    mode_popularity: Dict[str, int] = None
    
    def __post_init__(self):
        if self.top_scores is None:
            self.top_scores = []
        if self.mode_popularity is None:
            self.mode_popularity = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserBehaviorMetrics:
    """사용자 행동 지표"""
    daily_active_users: int = 0
    weekly_active_users: int = 0
    monthly_active_users: int = 0
    retention_rate: float = 0.0
    average_session_duration: float = 0.0
    bounce_rate: float = 0.0
    conversion_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """성능 지표"""
    average_response_time: float = 0.0
    peak_concurrent_users: int = 0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    database_query_time: float = 0.0
    websocket_connections: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContentMetrics:
    """콘텐츠 지표"""
    most_used_words: List[Dict[str, Any]] = None
    difficulty_distribution: Dict[str, int] = None
    item_usage_stats: Dict[str, int] = None
    mode_completion_rates: Dict[str, float] = None
    
    def __post_init__(self):
        if self.most_used_words is None:
            self.most_used_words = []
        if self.difficulty_distribution is None:
            self.difficulty_distribution = {}
        if self.item_usage_stats is None:
            self.item_usage_stats = {}
        if self.mode_completion_rates is None:
            self.mode_completion_rates = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnalyticsService:
    """분석 서비스"""
    
    def __init__(self):
        self.redis_client = get_redis()
        
        # 메트릭 저장 키
        self.metrics_prefix = "analytics:"
        self.events_prefix = "events:"
        self.aggregates_prefix = "aggregates:"
        
        # 실시간 이벤트 버퍼
        self.event_buffer = []
        self.buffer_size = 1000
    
    # === 이벤트 수집 ===
    
    async def track_event(self, event_type: str, user_id: Optional[int], 
                         data: Dict[str, Any], timestamp: Optional[datetime] = None):
        """이벤트 추적"""
        try:
            event = {
                "type": event_type,
                "user_id": user_id,
                "data": data,
                "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat()
            }
            
            # Redis에 이벤트 저장
            event_key = f"{self.events_prefix}{event_type}"
            self.redis_client.lpush(event_key, json.dumps(event, ensure_ascii=False))
            self.redis_client.ltrim(event_key, 0, 9999)  # 최대 10,000개 유지
            
            # 실시간 집계 업데이트
            await self._update_realtime_metrics(event_type, data)
            
            logger.debug(f"이벤트 추적: type={event_type}, user={user_id}")
            
        except Exception as e:
            logger.error(f"이벤트 추적 중 오류: {e}")
    
    async def _update_realtime_metrics(self, event_type: str, data: Dict[str, Any]):
        """실시간 메트릭 업데이트"""
        try:
            current_hour = datetime.now(timezone.utc).strftime("%Y%m%d%H")
            
            # 이벤트 카운트 증가
            counter_key = f"{self.aggregates_prefix}counter:{event_type}:{current_hour}"
            self.redis_client.incr(counter_key)
            self.redis_client.expire(counter_key, 86400)  # 24시간 TTL
            
            # 특정 이벤트별 추가 처리
            if event_type == "game_started":
                await self._track_game_started(data)
            elif event_type == "game_ended":
                await self._track_game_ended(data)
            elif event_type == "user_joined":
                await self._track_user_activity(data)
            elif event_type == "word_submitted":
                await self._track_word_submitted(data)
            elif event_type == "item_used":
                await self._track_item_used(data)
                
        except Exception as e:
            logger.error(f"실시간 메트릭 업데이트 중 오류: {e}")
    
    async def _track_game_started(self, data: Dict[str, Any]):
        """게임 시작 추적"""
        room_id = data.get("room_id")
        mode_type = data.get("mode_type", "classic")
        players_count = data.get("players_count", 0)
        
        # 활성 게임 수 증가
        self.redis_client.incr(f"{self.metrics_prefix}active_games")
        
        # 모드별 게임 수 증가
        mode_key = f"{self.metrics_prefix}mode_games:{mode_type}"
        self.redis_client.incr(mode_key)
        
        # 플레이어 수별 분포
        player_range = self._get_player_range(players_count)
        range_key = f"{self.metrics_prefix}player_range:{player_range}"
        self.redis_client.incr(range_key)
    
    async def _track_game_ended(self, data: Dict[str, Any]):
        """게임 종료 추적"""
        duration = data.get("duration", 0)
        total_words = data.get("total_words", 0)
        winner_score = data.get("winner_score", 0)
        mode_type = data.get("mode_type", "classic")
        
        # 활성 게임 수 감소
        self.redis_client.decr(f"{self.metrics_prefix}active_games")
        
        # 게임 지속 시간 통계
        duration_key = f"{self.metrics_prefix}game_duration"
        self._update_average_metric(duration_key, duration)
        
        # 단어 수 통계
        words_key = f"{self.metrics_prefix}words_per_game"
        self._update_average_metric(words_key, total_words)
        
        # 최고 점수 추적
        if winner_score > 0:
            score_key = f"{self.metrics_prefix}top_scores"
            self.redis_client.zadd(score_key, {str(winner_score): winner_score})
            self.redis_client.zremrangebyrank(score_key, 0, -101)  # 상위 100개만 유지
    
    async def _track_user_activity(self, data: Dict[str, Any]):
        """사용자 활동 추적"""
        user_id = data.get("user_id")
        if not user_id:
            return
        
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y%m%d")
        hour = now.strftime("%Y%m%d%H")
        
        # 일일 활성 사용자
        dau_key = f"{self.metrics_prefix}dau:{today}"
        self.redis_client.sadd(dau_key, str(user_id))
        self.redis_client.expire(dau_key, 172800)  # 48시간 TTL
        
        # 시간별 활성 사용자
        hau_key = f"{self.metrics_prefix}hau:{hour}"
        self.redis_client.sadd(hau_key, str(user_id))
        self.redis_client.expire(hau_key, 7200)  # 2시간 TTL
        
        # 동시 접속자 수
        concurrent_key = f"{self.metrics_prefix}concurrent_users"
        self.redis_client.sadd(concurrent_key, str(user_id))
        self.redis_client.expire(concurrent_key, 300)  # 5분 TTL
    
    async def _track_word_submitted(self, data: Dict[str, Any]):
        """단어 제출 추적"""
        word = data.get("word", "")
        difficulty = data.get("difficulty", 0)
        score = data.get("score", 0)
        
        if word:
            # 인기 단어 추적
            word_key = f"{self.metrics_prefix}popular_words"
            self.redis_client.zincrby(word_key, 1, word)
            self.redis_client.zremrangebyrank(word_key, 0, -1001)  # 상위 1000개만 유지
        
        # 난이도별 분포
        if difficulty > 0:
            diff_key = f"{self.metrics_prefix}difficulty_dist:{difficulty}"
            self.redis_client.incr(diff_key)
        
        # 점수 분포
        if score > 0:
            score_range = self._get_score_range(score)
            score_range_key = f"{self.metrics_prefix}score_range:{score_range}"
            self.redis_client.incr(score_range_key)
    
    async def _track_item_used(self, data: Dict[str, Any]):
        """아이템 사용 추적"""
        item_id = data.get("item_id")
        item_type = data.get("item_type", "unknown")
        
        if item_id:
            # 아이템 사용 횟수
            item_key = f"{self.metrics_prefix}item_usage:{item_id}"
            self.redis_client.incr(item_key)
        
        # 아이템 타입별 사용 횟수
        type_key = f"{self.metrics_prefix}item_type_usage:{item_type}"
        self.redis_client.incr(type_key)
    
    def _update_average_metric(self, key: str, value: float):
        """평균 메트릭 업데이트"""
        # 이동 평균 계산을 위한 값들 저장
        values_key = f"{key}:values"
        self.redis_client.lpush(values_key, str(value))
        self.redis_client.ltrim(values_key, 0, 999)  # 최대 1000개 값 유지
    
    def _get_player_range(self, count: int) -> str:
        """플레이어 수 범위 계산"""
        if count <= 2:
            return "1-2"
        elif count <= 4:
            return "3-4"
        elif count <= 6:
            return "5-6"
        else:
            return "7+"
    
    def _get_score_range(self, score: int) -> str:
        """점수 범위 계산"""
        if score < 100:
            return "0-99"
        elif score < 500:
            return "100-499"
        elif score < 1000:
            return "500-999"
        else:
            return "1000+"
    
    # === 데이터 조회 및 분석 ===
    
    async def get_game_metrics(self, period: AnalyticsPeriod = AnalyticsPeriod.DAILY) -> GameMetrics:
        """게임 메트릭 조회"""
        try:
            metrics = GameMetrics()
            
            # 활성 게임 수
            active_games = self.redis_client.get(f"{self.metrics_prefix}active_games")
            metrics.active_games = int(active_games) if active_games else 0
            
            # 모드별 인기도
            mode_popularity = {}
            mode_keys = self.redis_client.keys(f"{self.metrics_prefix}mode_games:*")
            for key in mode_keys:
                mode = key.decode().split(":")[-1]
                count = int(self.redis_client.get(key) or 0)
                mode_popularity[mode] = count
            metrics.mode_popularity = mode_popularity
            
            # 상위 점수
            top_scores_data = self.redis_client.zrevrange(
                f"{self.metrics_prefix}top_scores", 0, 9, withscores=True
            )
            metrics.top_scores = [int(score) for _, score in top_scores_data]
            
            # 평균 게임 시간
            duration_values = self.redis_client.lrange(
                f"{self.metrics_prefix}game_duration:values", 0, -1
            )
            if duration_values:
                durations = [float(v) for v in duration_values]
                metrics.average_game_duration = sum(durations) / len(durations)
            
            # 평균 단어 수
            words_values = self.redis_client.lrange(
                f"{self.metrics_prefix}words_per_game:values", 0, -1
            )
            if words_values:
                word_counts = [float(v) for v in words_values]
                metrics.average_words_per_game = sum(word_counts) / len(word_counts)
            
            # 데이터베이스에서 총 게임 수 조회
            db = next(get_db())
            total_games_result = db.execute(select(func.count(GameSession.id)))
            metrics.total_games = total_games_result.scalar() or 0
            
            return metrics
            
        except Exception as e:
            logger.error(f"게임 메트릭 조회 중 오류: {e}")
            return GameMetrics()
    
    async def get_user_behavior_metrics(self, period: AnalyticsPeriod = AnalyticsPeriod.DAILY) -> UserBehaviorMetrics:
        """사용자 행동 메트릭 조회"""
        try:
            metrics = UserBehaviorMetrics()
            now = datetime.now(timezone.utc)
            
            # 일일 활성 사용자
            today = now.strftime("%Y%m%d")
            dau_key = f"{self.metrics_prefix}dau:{today}"
            metrics.daily_active_users = self.redis_client.scard(dau_key)
            
            # 주간 활성 사용자 (최근 7일)
            wau_users = set()
            for i in range(7):
                date = (now - timedelta(days=i)).strftime("%Y%m%d")
                day_users = self.redis_client.smembers(f"{self.metrics_prefix}dau:{date}")
                wau_users.update(day_users)
            metrics.weekly_active_users = len(wau_users)
            
            # 월간 활성 사용자 (최근 30일)
            mau_users = set()
            for i in range(30):
                date = (now - timedelta(days=i)).strftime("%Y%m%d")
                day_users = self.redis_client.smembers(f"{self.metrics_prefix}dau:{date}")
                mau_users.update(day_users)
            metrics.monthly_active_users = len(mau_users)
            
            # 동시 접속자 수
            concurrent_key = f"{self.metrics_prefix}concurrent_users"
            concurrent_count = self.redis_client.scard(concurrent_key)
            
            # 리텐션률 계산 (간단한 버전)
            if metrics.weekly_active_users > 0:
                metrics.retention_rate = metrics.daily_active_users / metrics.weekly_active_users
            
            return metrics
            
        except Exception as e:
            logger.error(f"사용자 행동 메트릭 조회 중 오류: {e}")
            return UserBehaviorMetrics()
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭 조회"""
        try:
            metrics = PerformanceMetrics()
            
            # 동시 접속자 수
            concurrent_key = f"{self.metrics_prefix}concurrent_users"
            metrics.websocket_connections = self.redis_client.scard(concurrent_key)
            
            # 캐시 성능 (캐시 서비스에서 가져오기)
            try:
                from services.cache_service import get_cache_service
                cache_service = get_cache_service()
                cache_metrics = await cache_service.get_performance_metrics()
                metrics.cache_hit_rate = cache_metrics["cache_stats"]["hit_rate"]
            except Exception:
                metrics.cache_hit_rate = 0.0
            
            # Redis 성능 정보
            try:
                redis_info = self.redis_client.info()
                metrics.peak_concurrent_users = redis_info.get("connected_clients", 0)
            except Exception:
                pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"성능 메트릭 조회 중 오류: {e}")
            return PerformanceMetrics()
    
    async def get_content_metrics(self) -> ContentMetrics:
        """콘텐츠 메트릭 조회"""
        try:
            metrics = ContentMetrics()
            
            # 인기 단어 Top 20
            popular_words = self.redis_client.zrevrange(
                f"{self.metrics_prefix}popular_words", 0, 19, withscores=True
            )
            metrics.most_used_words = [
                {"word": word.decode(), "count": int(count)}
                for word, count in popular_words
            ]
            
            # 난이도 분포
            difficulty_dist = {}
            for i in range(1, 6):  # 1~5 난이도
                count = self.redis_client.get(f"{self.metrics_prefix}difficulty_dist:{i}")
                difficulty_dist[f"level_{i}"] = int(count) if count else 0
            metrics.difficulty_distribution = difficulty_dist
            
            # 아이템 사용 통계
            item_usage = {}
            item_keys = self.redis_client.keys(f"{self.metrics_prefix}item_usage:*")
            for key in item_keys[:20]:  # 상위 20개
                item_id = key.decode().split(":")[-1]
                count = int(self.redis_client.get(key) or 0)
                item_usage[f"item_{item_id}"] = count
            metrics.item_usage_stats = item_usage
            
            return metrics
            
        except Exception as e:
            logger.error(f"콘텐츠 메트릭 조회 중 오류: {e}")
            return ContentMetrics()
    
    # === 리포트 생성 ===
    
    async def generate_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 생성"""
        try:
            game_metrics = await self.get_game_metrics()
            user_metrics = await self.get_user_behavior_metrics()
            performance_metrics = await self.get_performance_metrics()
            content_metrics = await self.get_content_metrics()
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "game_metrics": game_metrics.to_dict(),
                "user_behavior": user_metrics.to_dict(),
                "performance": performance_metrics.to_dict(),
                "content": content_metrics.to_dict(),
                "summary": {
                    "health_score": self._calculate_health_score(
                        performance_metrics, user_metrics
                    ),
                    "trends": await self._get_trends(),
                    "alerts": await self._get_alerts()
                }
            }
            
        except Exception as e:
            logger.error(f"대시보드 데이터 생성 중 오류: {e}")
            return {"error": str(e)}
    
    def _calculate_health_score(self, performance: PerformanceMetrics, 
                               user_behavior: UserBehaviorMetrics) -> float:
        """시스템 건강도 점수 계산"""
        score = 100.0
        
        # 오류율 페널티
        if performance.error_rate > 0.05:  # 5% 초과
            score -= min(20, performance.error_rate * 100)
        
        # 캐시 적중률 보너스
        if performance.cache_hit_rate > 0.8:  # 80% 초과
            score += 5
        elif performance.cache_hit_rate < 0.5:  # 50% 미만
            score -= 10
        
        # 사용자 증가율 보너스
        if user_behavior.daily_active_users > user_behavior.weekly_active_users * 0.3:
            score += 10
        
        return max(0, min(100, score))
    
    async def _get_trends(self) -> Dict[str, str]:
        """트렌드 분석"""
        return {
            "user_growth": "stable",
            "game_popularity": "increasing",
            "performance": "good"
        }
    
    async def _get_alerts(self) -> List[Dict[str, str]]:
        """알림 목록"""
        alerts = []
        
        # 동시 접속자 수 체크
        concurrent_users = self.redis_client.scard(f"{self.metrics_prefix}concurrent_users")
        if concurrent_users > 1000:
            alerts.append({
                "type": "warning",
                "message": f"높은 동시 접속자 수: {concurrent_users}명"
            })
        
        return alerts
    
    # === 정리 작업 ===
    
    async def cleanup_old_data(self, days: int = 30):
        """오래된 데이터 정리"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff_date.strftime("%Y%m%d")
            
            # 오래된 DAU 키 삭제
            pattern = f"{self.metrics_prefix}dau:*"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                date_str = key.decode().split(":")[-1]
                if date_str < cutoff_str:
                    self.redis_client.delete(key)
            
            logger.info(f"{days}일 이전 데이터 정리 완료")
            
        except Exception as e:
            logger.error(f"데이터 정리 중 오류: {e}")


# 전역 분석 서비스 인스턴스
analytics_service = AnalyticsService()


def get_analytics_service() -> AnalyticsService:
    """분석 서비스 의존성"""
    return analytics_service