# 어드민 대시보드 및 게임 분석 시스템 구현 가이드

## 개요

KKUA의 운영 및 관리를 위한 종합적인 어드민 대시보드를 구현합니다. 실시간 모니터링, 사용자 관리, 게임 분석, 시스템 성능 추적 등의 기능을 제공하여 효율적인 서비스 운영을 지원합니다.

## 주요 기능

### 1. 실시간 모니터링
- **시스템 상태**: 서버 성능, DB 연결, Redis 상태
- **사용자 활동**: 접속자 수, 게임 진행 현황
- **트래픽 모니터링**: API 호출량, WebSocket 연결 수

### 2. 사용자 관리
- **사용자 목록**: 전체 사용자 조회 및 검색
- **계정 관리**: 계정 정지, 차단, 권한 관리
- **활동 로그**: 사용자별 활동 기록

### 3. 게임 분석
- **게임 통계**: 게임 수, 평균 플레이 시간, 인기 단어
- **플레이어 분석**: 접속 패턴, 게임 성과 분석
- **수익 분석**: 토너먼트 참가비, 아이템 사용량

### 4. 콘텐츠 관리
- **토너먼트 관리**: 공식 토너먼트 생성 및 관리
- **업적 관리**: 업적 생성, 수정, 비활성화
- **공지사항**: 시스템 공지 및 이벤트 관리

---

## 데이터베이스 설계

### 어드민 관련 모델

```python
# backend/models/admin_model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from backend.models.base import Base
from datetime import datetime
from enum import Enum

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    ANALYST = "analyst"

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    admin_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 권한 및 역할
    role = Column(SQLEnum(AdminRole), default=AdminRole.MODERATOR)
    permissions = Column(JSON)  # 세부 권한 설정
    is_active = Column(Boolean, default=True)
    
    # 개인 정보
    full_name = Column(String(100))
    avatar_url = Column(String(255))
    
    # 로그인 정보
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("admin_users.admin_id"))
    
    # 관계 설정
    creator = relationship("AdminUser", remote_side=[admin_id])
    created_admins = relationship("AdminUser", remote_side=[created_by])
    
    def __repr__(self):
        return f"<AdminUser {self.username} ({self.role})>"

class AdminSession(Base):
    __tablename__ = "admin_sessions"
    
    session_id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("admin_users.admin_id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    
    # 세션 정보
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    admin = relationship("AdminUser")

class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"
    
    log_id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("admin_users.admin_id"), nullable=False)
    
    # 액션 정보
    action_type = Column(String(50), nullable=False)  # user_ban, tournament_create 등
    target_type = Column(String(30))  # user, tournament, system 등
    target_id = Column(String(50))    # 대상 ID
    
    # 상세 정보
    description = Column(Text)
    old_values = Column(JSON)  # 변경 전 값
    new_values = Column(JSON)  # 변경 후 값
    
    # 메타데이터
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    admin = relationship("AdminUser")
    
    def __repr__(self):
        return f"<AdminActionLog {self.action_type} by {self.admin_id}>"

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    metric_id = Column(Integer, primary_key=True)
    
    # 메트릭 정보
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(255), nullable=False)
    metric_type = Column(String(30), nullable=False)  # counter, gauge, histogram
    
    # 태그 및 라벨
    tags = Column(JSON)  # {"service": "api", "endpoint": "/games"}
    
    # 수집 시간
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemMetric {self.metric_name}: {self.metric_value}>"

class Announcement(Base):
    __tablename__ = "announcements"
    
    announcement_id = Column(Integer, primary_key=True)
    
    # 공지 내용
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(30), default="general")  # general, maintenance, event
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # 표시 설정
    is_active = Column(Boolean, default=True)
    is_popup = Column(Boolean, default=False)
    target_users = Column(JSON)  # 특정 사용자 대상 (null이면 전체)
    
    # 시간 설정
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    # 작성자 정보
    created_by = Column(Integer, ForeignKey("admin_users.admin_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # 관계 설정
    creator = relationship("AdminUser")

class UserAction(Base):
    __tablename__ = "user_actions"
    
    action_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    
    # 액션 정보
    action_type = Column(String(50), nullable=False)  # login, game_join, word_submit 등
    details = Column(JSON)  # 액션별 상세 정보
    
    # 메타데이터
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    guest = relationship("Guest")
    
    def __repr__(self):
        return f"<UserAction {self.action_type} by {self.guest_id}>"
```

---

## 백엔드 서비스 구현

### AdminAnalyticsService 구현

```python
# backend/services/admin_analytics_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, text
from backend.models.admin_model import SystemMetric, UserAction
from backend.models.guest_model import Guest
from backend.models.gameroom_model import Gameroom
from backend.models.game_log_model import GameLog
from backend.models.friend_model import PlayerSession, OnlineStatus
from backend.services.redis_service import RedisService
from datetime import datetime, timedelta
import json
import psutil
import asyncio

class AdminAnalyticsService:
    """어드민 분석 및 모니터링 서비스"""
    
    def __init__(self, db: Session, redis_service: RedisService):
        self.db = db
        self.redis = redis_service
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """대시보드 개요 정보"""
        
        # 기본 통계 (병렬 처리)
        tasks = [
            self._get_user_statistics(),
            self._get_game_statistics(),
            self._get_system_health(),
            self._get_real_time_metrics()
        ]
        
        user_stats, game_stats, system_health, real_time = await asyncio.gather(*tasks)
        
        return {
            "users": user_stats,
            "games": game_stats,
            "system": system_health,
            "real_time": real_time,
            "last_updated": datetime.utcnow()
        }
    
    async def _get_user_statistics(self) -> Dict[str, Any]:
        """사용자 통계"""
        
        # 전체 사용자 수
        total_users = self.db.query(Guest).count()
        
        # 오늘 신규 가입자
        today = datetime.utcnow().date()
        new_users_today = self.db.query(Guest).filter(
            func.date(Guest.created_at) == today
        ).count()
        
        # 이번 주 신규 가입자
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = self.db.query(Guest).filter(
            Guest.created_at >= week_ago
        ).count()
        
        # 현재 온라인 사용자
        online_users = self.db.query(PlayerSession).filter(
            PlayerSession.status.in_([OnlineStatus.ONLINE, OnlineStatus.IN_GAME]),
            PlayerSession.last_activity >= datetime.utcnow() - timedelta(minutes=5)
        ).count()
        
        # 활성 사용자 (최근 24시간 내 활동)
        active_users = self.db.query(Guest).join(PlayerSession).filter(
            PlayerSession.last_activity >= datetime.utcnow() - timedelta(hours=24)
        ).distinct().count()
        
        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "new_users_week": new_users_week,
            "online_users": online_users,
            "active_users_24h": active_users,
            "user_growth_rate": self._calculate_growth_rate("users", 7)
        }
    
    async def _get_game_statistics(self) -> Dict[str, Any]:
        """게임 통계"""
        
        # 전체 게임 수
        total_games = self.db.query(GameLog).count()
        
        # 오늘 게임 수
        today = datetime.utcnow().date()
        games_today = self.db.query(GameLog).filter(
            func.date(GameLog.created_at) == today
        ).count()
        
        # 현재 진행 중인 게임
        active_games = await self.redis.scard("active_games")
        
        # 현재 대기 중인 방
        waiting_rooms = self.db.query(Gameroom).filter(
            Gameroom.status == "waiting"
        ).count()
        
        # 평균 게임 시간 (최근 100게임)
        recent_games = self.db.query(GameLog.duration_seconds).filter(
            GameLog.duration_seconds.isnot(None)
        ).order_by(desc(GameLog.created_at)).limit(100).all()
        
        avg_duration = sum(game.duration_seconds for game in recent_games) / len(recent_games) if recent_games else 0
        
        # 인기 게임 모드
        popular_modes = self.db.query(
            Gameroom.game_mode, func.count(Gameroom.game_mode).label('count')
        ).group_by(Gameroom.game_mode).order_by(desc('count')).limit(5).all()
        
        return {
            "total_games": total_games,
            "games_today": games_today,
            "active_games": active_games,
            "waiting_rooms": waiting_rooms,
            "average_duration_minutes": round(avg_duration / 60, 1),
            "popular_game_modes": [{"mode": mode, "count": count} for mode, count in popular_modes],
            "game_growth_rate": self._calculate_growth_rate("games", 7)
        }
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """시스템 상태"""
        
        # CPU 및 메모리 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 데이터베이스 연결 상태
        try:
            self.db.execute(text("SELECT 1"))
            db_status = "healthy"
            db_response_time = await self._measure_db_response_time()
        except Exception as e:
            db_status = "error"
            db_response_time = None
        
        # Redis 연결 상태
        try:
            await self.redis.ping()
            redis_status = "healthy"
            redis_response_time = await self._measure_redis_response_time()
        except Exception:
            redis_status = "error"
            redis_response_time = None
        
        # WebSocket 연결 수
        websocket_connections = await self._get_websocket_connection_count()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": (disk.used / disk.total) * 100,
            "database": {
                "status": db_status,
                "response_time_ms": db_response_time
            },
            "redis": {
                "status": redis_status,
                "response_time_ms": redis_response_time
            },
            "websocket_connections": websocket_connections,
            "uptime_hours": self._get_system_uptime_hours()
        }
    
    async def _get_real_time_metrics(self) -> Dict[str, Any]:
        """실시간 메트릭"""
        
        # API 호출량 (최근 1시간)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        api_calls = await self._get_api_call_count(hour_ago)
        
        # 에러율 (최근 1시간)
        error_rate = await self._get_error_rate(hour_ago)
        
        # 평균 응답 시간
        avg_response_time = await self._get_average_response_time(hour_ago)
        
        return {
            "api_calls_per_hour": api_calls,
            "error_rate_percent": error_rate,
            "avg_response_time_ms": avg_response_time,
            "peak_concurrent_users": await self._get_peak_concurrent_users(),
            "data_transfer_mb": await self._get_data_transfer_volume()
        }
    
    async def get_user_analytics(self, days: int = 30) -> Dict[str, Any]:
        """사용자 분석 데이터"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 일별 신규 가입자
        daily_registrations = self.db.query(
            func.date(Guest.created_at).label('date'),
            func.count(Guest.guest_id).label('count')
        ).filter(
            Guest.created_at >= start_date
        ).group_by(func.date(Guest.created_at)).order_by('date').all()
        
        # 일별 활성 사용자
        daily_active_users = self.db.query(
            func.date(UserAction.created_at).label('date'),
            func.count(func.distinct(UserAction.guest_id)).label('count')
        ).filter(
            UserAction.created_at >= start_date
        ).group_by(func.date(UserAction.created_at)).order_by('date').all()
        
        # 사용자 유지율 (cohort 분석)
        retention_data = await self._calculate_user_retention(days)
        
        # 인기 활동
        popular_activities = self.db.query(
            UserAction.action_type,
            func.count(UserAction.action_id).label('count')
        ).filter(
            UserAction.created_at >= start_date
        ).group_by(UserAction.action_type).order_by(desc('count')).limit(10).all()
        
        # 지역별 사용자 (IP 기반)
        geographic_data = await self._get_geographic_distribution(days)
        
        return {
            "daily_registrations": [
                {"date": str(date), "count": count} 
                for date, count in daily_registrations
            ],
            "daily_active_users": [
                {"date": str(date), "count": count} 
                for date, count in daily_active_users
            ],
            "retention_analysis": retention_data,
            "popular_activities": [
                {"activity": activity, "count": count} 
                for activity, count in popular_activities
            ],
            "geographic_distribution": geographic_data
        }
    
    async def get_game_analytics(self, days: int = 30) -> Dict[str, Any]:
        """게임 분석 데이터"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 일별 게임 수
        daily_games = self.db.query(
            func.date(GameLog.created_at).label('date'),
            func.count(GameLog.log_id).label('count')
        ).filter(
            GameLog.created_at >= start_date
        ).group_by(func.date(GameLog.created_at)).order_by('date').all()
        
        # 게임 모드별 통계
        mode_statistics = self.db.query(
            GameLog.game_mode,
            func.count(GameLog.log_id).label('game_count'),
            func.avg(GameLog.duration_seconds).label('avg_duration'),
            func.avg(func.json_array_length(GameLog.participant_data)).label('avg_players')
        ).filter(
            GameLog.created_at >= start_date
        ).group_by(GameLog.game_mode).all()
        
        # 인기 단어 Top 50
        popular_words = await self._get_popular_words(days)
        
        # 게임 완료율
        completion_rate = await self._calculate_game_completion_rate(days)
        
        # 평균 점수 분포
        score_distribution = await self._get_score_distribution(days)
        
        # 피크 시간대 분석
        peak_hours = await self._analyze_peak_gaming_hours(days)
        
        return {
            "daily_games": [
                {"date": str(date), "count": count} 
                for date, count in daily_games
            ],
            "mode_statistics": [
                {
                    "mode": mode,
                    "game_count": game_count,
                    "avg_duration_minutes": round(avg_duration / 60, 1) if avg_duration else 0,
                    "avg_players": round(avg_players, 1) if avg_players else 0
                }
                for mode, game_count, avg_duration, avg_players in mode_statistics
            ],
            "popular_words": popular_words,
            "completion_rate_percent": completion_rate,
            "score_distribution": score_distribution,
            "peak_gaming_hours": peak_hours
        }
    
    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """성능 메트릭"""
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 시간대별 API 응답 시간
        response_times = await self._get_hourly_response_times(start_time)
        
        # 에러 로그 분석
        error_analysis = await self._analyze_errors(start_time)
        
        # 데이터베이스 성능
        db_performance = await self._get_database_performance(start_time)
        
        # Redis 성능
        redis_performance = await self._get_redis_performance(start_time)
        
        # 네트워크 트래픽
        network_stats = await self._get_network_statistics(start_time)
        
        return {
            "response_times": response_times,
            "error_analysis": error_analysis,
            "database_performance": db_performance,
            "redis_performance": redis_performance,
            "network_statistics": network_stats,
            "system_resources": {
                "cpu_usage": await self._get_cpu_usage_history(hours),
                "memory_usage": await self._get_memory_usage_history(hours),
                "disk_io": await self._get_disk_io_history(hours)
            }
        }
    
    def _calculate_growth_rate(self, metric_type: str, days: int) -> float:
        """성장률 계산"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        previous_start = start_date - timedelta(days=days)
        
        if metric_type == "users":
            current_count = self.db.query(Guest).filter(
                Guest.created_at >= start_date,
                Guest.created_at <= end_date
            ).count()
            
            previous_count = self.db.query(Guest).filter(
                Guest.created_at >= previous_start,
                Guest.created_at <= start_date
            ).count()
        
        elif metric_type == "games":
            current_count = self.db.query(GameLog).filter(
                GameLog.created_at >= start_date,
                GameLog.created_at <= end_date
            ).count()
            
            previous_count = self.db.query(GameLog).filter(
                GameLog.created_at >= previous_start,
                GameLog.created_at <= start_date
            ).count()
        
        else:
            return 0.0
        
        if previous_count == 0:
            return 100.0 if current_count > 0 else 0.0
        
        return ((current_count - previous_count) / previous_count) * 100
    
    async def _measure_db_response_time(self) -> Optional[float]:
        """데이터베이스 응답 시간 측정"""
        try:
            start_time = datetime.utcnow()
            self.db.execute(text("SELECT 1"))
            end_time = datetime.utcnow()
            return (end_time - start_time).total_seconds() * 1000
        except Exception:
            return None
    
    async def _measure_redis_response_time(self) -> Optional[float]:
        """Redis 응답 시간 측정"""
        try:
            import time
            start_time = time.time()
            await self.redis.ping()
            end_time = time.time()
            return (end_time - start_time) * 1000
        except Exception:
            return None
    
    async def _get_popular_words(self, days: int) -> List[Dict[str, Any]]:
        """인기 단어 분석"""
        
        # Redis에서 단어 사용 통계 조회
        # 실제 구현에서는 게임 로그에서 단어 데이터를 추출해야 함
        try:
            word_stats = await self.redis.zrevrange("popular_words", 0, 49, withscores=True)
            return [
                {"word": word.decode(), "count": int(score)}
                for word, score in word_stats
            ]
        except Exception:
            return []
    
    async def record_user_action(self, guest_id: int, action_type: str, 
                               details: Dict[str, Any], request_info: Dict[str, str]):
        """사용자 액션 기록"""
        
        action = UserAction(
            guest_id=guest_id,
            action_type=action_type,
            details=details,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            session_id=request_info.get("session_id")
        )
        
        self.db.add(action)
        self.db.commit()
        
        # 실시간 메트릭 업데이트
        await self._update_real_time_metrics(action_type)
    
    async def record_system_metric(self, metric_name: str, value: Any, 
                                 metric_type: str = "gauge", tags: Dict[str, str] = None):
        """시스템 메트릭 기록"""
        
        metric = SystemMetric(
            metric_name=metric_name,
            metric_value=str(value),
            metric_type=metric_type,
            tags=tags or {}
        )
        
        self.db.add(metric)
        self.db.commit()
        
        # Redis에도 최신 값 저장 (빠른 조회용)
        await self.redis.set(f"metric:{metric_name}", str(value), ex=3600)
```

### AdminUserService 구현

```python
# backend/services/admin_user_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from backend.models.admin_model import AdminUser, AdminSession, AdminActionLog, AdminRole
from backend.models.guest_model import Guest
from backend.services.security_service import SecurityService
from datetime import datetime, timedelta
import secrets
import hashlib

class AdminUserService:
    """어드민 사용자 관리 서비스"""
    
    def __init__(self, db: Session, security_service: SecurityService):
        self.db = db
        self.security = security_service
    
    async def authenticate_admin(self, username: str, password: str) -> Dict[str, Any]:
        """어드민 로그인 인증"""
        
        admin = self.db.query(AdminUser).filter(
            AdminUser.username == username,
            AdminUser.is_active == True
        ).first()
        
        if not admin:
            return {"success": False, "message": "존재하지 않는 사용자입니다"}
        
        if not self.security.verify_password(password, admin.password_hash):
            return {"success": False, "message": "비밀번호가 올바르지 않습니다"}
        
        # 세션 토큰 생성
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=8)  # 8시간 유효
        
        # 세션 저장
        session = AdminSession(
            admin_id=admin.admin_id,
            session_token=session_token,
            expires_at=expires_at
        )
        
        self.db.add(session)
        
        # 로그인 정보 업데이트
        admin.last_login = datetime.utcnow()
        admin.login_count += 1
        
        self.db.commit()
        
        # 로그 기록
        await self.log_admin_action(
            admin.admin_id, "admin_login", "system", None,
            f"관리자 {username} 로그인"
        )
        
        return {
            "success": True,
            "session_token": session_token,
            "admin": {
                "admin_id": admin.admin_id,
                "username": admin.username,
                "role": admin.role,
                "permissions": admin.permissions,
                "full_name": admin.full_name
            }
        }
    
    async def get_admin_by_session(self, session_token: str) -> Optional[AdminUser]:
        """세션 토큰으로 어드민 조회"""
        
        session = self.db.query(AdminSession, AdminUser).join(
            AdminUser, AdminSession.admin_id == AdminUser.admin_id
        ).filter(
            AdminSession.session_token == session_token,
            AdminSession.expires_at > datetime.utcnow(),
            AdminUser.is_active == True
        ).first()
        
        if not session:
            return None
        
        # 마지막 활동 시간 업데이트
        session[0].last_activity = datetime.utcnow()
        self.db.commit()
        
        return session[1]
    
    async def manage_user(self, admin_id: int, user_id: int, action: str, 
                         reason: str = None, duration: int = None) -> Dict[str, Any]:
        """사용자 관리 (정지, 차단, 해제 등)"""
        
        admin = self.db.query(AdminUser).filter(AdminUser.admin_id == admin_id).first()
        if not admin:
            return {"success": False, "message": "권한이 없습니다"}
        
        user = self.db.query(Guest).filter(Guest.guest_id == user_id).first()
        if not user:
            return {"success": False, "message": "존재하지 않는 사용자입니다"}
        
        # 권한 확인
        if not self._check_permission(admin, "user_management"):
            return {"success": False, "message": "사용자 관리 권한이 없습니다"}
        
        old_values = {
            "is_active": getattr(user, 'is_active', True),
            "banned_until": getattr(user, 'banned_until', None)
        }
        
        # 액션 수행
        if action == "ban":
            if duration:
                user.banned_until = datetime.utcnow() + timedelta(days=duration)
            else:
                user.banned_until = datetime(2099, 12, 31)  # 영구 정지
            
        elif action == "unban":
            user.banned_until = None
            
        elif action == "deactivate":
            user.is_active = False
            
        elif action == "activate":
            user.is_active = True
            
        else:
            return {"success": False, "message": "지원하지 않는 액션입니다"}
        
        new_values = {
            "is_active": getattr(user, 'is_active', True),
            "banned_until": user.banned_until
        }
        
        self.db.commit()
        
        # 액션 로그 기록
        await self.log_admin_action(
            admin_id, f"user_{action}", "user", str(user_id),
            f"사용자 {user.nickname}에 대한 {action} 실행. 사유: {reason}",
            old_values, new_values
        )
        
        return {
            "success": True,
            "message": f"사용자 {action} 처리가 완료되었습니다",
            "user_id": user_id,
            "action": action
        }
    
    async def get_user_list(self, page: int = 1, limit: int = 50, 
                          search: str = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """사용자 목록 조회"""
        
        query = self.db.query(Guest)
        
        # 검색 조건
        if search:
            query = query.filter(
                or_(
                    Guest.nickname.contains(search),
                    Guest.guest_id == int(search) if search.isdigit() else False
                )
            )
        
        # 필터 조건
        if filters:
            if filters.get("is_banned"):
                query = query.filter(Guest.banned_until > datetime.utcnow())
            
            if filters.get("is_active") is not None:
                query = query.filter(Guest.is_active == filters["is_active"])
            
            if filters.get("created_after"):
                query = query.filter(Guest.created_at >= filters["created_after"])
        
        # 전체 수 계산
        total_count = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        users = query.order_by(desc(Guest.created_at)).offset(offset).limit(limit).all()
        
        return {
            "users": [
                {
                    "guest_id": user.guest_id,
                    "nickname": user.nickname,
                    "is_active": getattr(user, 'is_active', True),
                    "is_banned": user.banned_until and user.banned_until > datetime.utcnow(),
                    "banned_until": user.banned_until,
                    "created_at": user.created_at,
                    "last_login": getattr(user, 'last_login', None)
                }
                for user in users
            ],
            "pagination": {
                "current_page": page,
                "total_pages": (total_count + limit - 1) // limit,
                "total_count": total_count,
                "has_next": page * limit < total_count,
                "has_prev": page > 1
            }
        }
    
    async def get_admin_action_logs(self, admin_id: Optional[int] = None, 
                                  action_type: Optional[str] = None,
                                  days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """어드민 액션 로그 조회"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(AdminActionLog, AdminUser).join(
            AdminUser, AdminActionLog.admin_id == AdminUser.admin_id
        ).filter(AdminActionLog.created_at >= start_date)
        
        if admin_id:
            query = query.filter(AdminActionLog.admin_id == admin_id)
        
        if action_type:
            query = query.filter(AdminActionLog.action_type == action_type)
        
        logs = query.order_by(desc(AdminActionLog.created_at)).limit(limit).all()
        
        return [
            {
                "log_id": log.log_id,
                "admin_username": admin.username,
                "action_type": log.action_type,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "description": log.description,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "created_at": log.created_at
            }
            for log, admin in logs
        ]
    
    async def log_admin_action(self, admin_id: int, action_type: str, 
                             target_type: str, target_id: Optional[str],
                             description: str, old_values: Dict[str, Any] = None,
                             new_values: Dict[str, Any] = None):
        """어드민 액션 로그 기록"""
        
        log = AdminActionLog(
            admin_id=admin_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            description=description,
            old_values=old_values,
            new_values=new_values
        )
        
        self.db.add(log)
        self.db.commit()
    
    def _check_permission(self, admin: AdminUser, permission: str) -> bool:
        """권한 확인"""
        
        # 슈퍼 어드민은 모든 권한
        if admin.role == AdminRole.SUPER_ADMIN:
            return True
        
        # 역할별 기본 권한
        role_permissions = {
            AdminRole.ADMIN: [
                "user_management", "content_management", "system_monitoring",
                "tournament_management", "analytics_view"
            ],
            AdminRole.MODERATOR: [
                "user_management", "content_management"
            ],
            AdminRole.ANALYST: [
                "analytics_view", "system_monitoring"
            ]
        }
        
        default_permissions = role_permissions.get(admin.role, [])
        
        # 개별 권한 설정 확인
        custom_permissions = admin.permissions or {}
        
        return (permission in default_permissions or 
                custom_permissions.get(permission, False))
```

---

## API 엔드포인트 구현

### Admin API Router

```python
# backend/routers/admin_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from backend.services.admin_analytics_service import AdminAnalyticsService
from backend.services.admin_user_service import AdminUserService
from backend.services.security_service import SecurityService
from backend.dependencies import get_db
from backend.schemas.admin_schema import (
    AdminLoginSchema, UserManagementSchema, AdminDashboardResponse
)
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["admin"])

def get_admin_services(db: Session = Depends(get_db)):
    from backend.services.redis_service import RedisService
    redis_service = RedisService()
    security_service = SecurityService()
    
    analytics_service = AdminAnalyticsService(db, redis_service)
    user_service = AdminUserService(db, security_service)
    
    return analytics_service, user_service

async def require_admin_auth(request: Request, db: Session = Depends(get_db)):
    """어드민 인증 미들웨어"""
    session_token = request.cookies.get("admin_session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="관리자 인증이 필요합니다")
    
    _, user_service = get_admin_services(db)
    admin = await user_service.get_admin_by_session(session_token)
    
    if not admin:
        raise HTTPException(status_code=401, detail="유효하지 않은 세션입니다")
    
    return admin

@router.post("/login")
async def admin_login(
    login_data: AdminLoginSchema,
    db: Session = Depends(get_db)
):
    """어드민 로그인"""
    _, user_service = get_admin_services(db)
    
    result = await user_service.authenticate_admin(
        login_data.username, login_data.password
    )
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    
    response = {"status": "success", "data": result}
    
    # 쿠키에 세션 토큰 설정
    from fastapi import Response
    response_obj = Response(content=str(response))
    response_obj.set_cookie(
        "admin_session_token",
        result["session_token"],
        httponly=True,
        secure=True,
        max_age=8 * 3600  # 8시간
    )
    
    return response

@router.get("/dashboard")
async def get_dashboard(
    analytics_service, _ = Depends(get_admin_services),
    admin = Depends(require_admin_auth)
):
    """대시보드 데이터 조회"""
    
    dashboard_data = await analytics_service.get_dashboard_overview()
    
    return {"status": "success", "data": dashboard_data}

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_banned: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    user_service = Depends(lambda: get_admin_services()[1]),
    admin = Depends(require_admin_auth)
):
    """사용자 목록 조회"""
    
    filters = {}
    if is_banned is not None:
        filters["is_banned"] = is_banned
    if is_active is not None:
        filters["is_active"] = is_active
    
    users_data = await user_service.get_user_list(
        page=page, limit=limit, search=search, filters=filters
    )
    
    return {"status": "success", "data": users_data}

@router.post("/users/{user_id}/manage")
async def manage_user(
    user_id: int,
    management_data: UserManagementSchema,
    user_service = Depends(lambda: get_admin_services()[1]),
    admin = Depends(require_admin_auth)
):
    """사용자 관리 (정지, 차단, 해제)"""
    
    result = await user_service.manage_user(
        admin_id=admin.admin_id,
        user_id=user_id,
        action=management_data.action,
        reason=management_data.reason,
        duration=management_data.duration
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"status": "success", "data": result}

@router.get("/analytics/users")
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    analytics_service = Depends(lambda: get_admin_services()[0]),
    admin = Depends(require_admin_auth)
):
    """사용자 분석 데이터"""
    
    analytics_data = await analytics_service.get_user_analytics(days)
    
    return {"status": "success", "data": analytics_data}

@router.get("/analytics/games")
async def get_game_analytics(
    days: int = Query(30, ge=1, le=365),
    analytics_service = Depends(lambda: get_admin_services()[0]),
    admin = Depends(require_admin_auth)
):
    """게임 분석 데이터"""
    
    analytics_data = await analytics_service.get_game_analytics(days)
    
    return {"status": "success", "data": analytics_data}

@router.get("/analytics/performance")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168),
    analytics_service = Depends(lambda: get_admin_services()[0]),
    admin = Depends(require_admin_auth)
):
    """성능 메트릭"""
    
    metrics_data = await analytics_service.get_performance_metrics(hours)
    
    return {"status": "success", "data": metrics_data}

@router.get("/logs/actions")
async def get_admin_action_logs(
    admin_id: Optional[int] = Query(None),
    action_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    user_service = Depends(lambda: get_admin_services()[1]),
    admin = Depends(require_admin_auth)
):
    """어드민 액션 로그 조회"""
    
    logs = await user_service.get_admin_action_logs(
        admin_id=admin_id,
        action_type=action_type,
        days=days,
        limit=limit
    )
    
    return {"status": "success", "data": {"logs": logs}}
```

---

## 프론트엔드 구현

### AdminDashboard 컴포넌트

```javascript
// frontend/src/Pages/Admin/AdminDashboard.js
import React, { useState, useEffect } from 'react';
import { getAdminDashboard, getUserAnalytics, getGameAnalytics } from '../../Api/adminApi';
import DashboardMetrics from './components/DashboardMetrics';
import UserAnalyticsChart from './components/UserAnalyticsChart';
import GameAnalyticsChart from './components/GameAnalyticsChart';
import SystemHealthPanel from './components/SystemHealthPanel';
import RealtimeUpdates from './components/RealtimeUpdates';

const AdminDashboard = () => {
    const [dashboardData, setDashboardData] = useState(null);
    const [userAnalytics, setUserAnalytics] = useState(null);
    const [gameAnalytics, setGameAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');
    const [refreshInterval, setRefreshInterval] = useState(30); // 30초

    useEffect(() => {
        loadDashboardData();
        
        // 자동 새로고침 설정
        const interval = setInterval(loadDashboardData, refreshInterval * 1000);
        return () => clearInterval(interval);
    }, [refreshInterval]);

    const loadDashboardData = async () => {
        try {
            const [dashboardResponse, userResponse, gameResponse] = await Promise.all([
                getAdminDashboard(),
                getUserAnalytics({ days: 30 }),
                getGameAnalytics({ days: 30 })
            ]);

            setDashboardData(dashboardResponse.data);
            setUserAnalytics(userResponse.data);
            setGameAnalytics(gameResponse.data);
        } catch (error) {
            console.error('대시보드 데이터 로드 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num) => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    };

    const getStatusColor = (status) => {
        return status === 'healthy' ? 'text-green-600' : 'text-red-600';
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard min-h-screen bg-gray-50">
            {/* 헤더 */}
            <div className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-4">
                        <h1 className="text-2xl font-bold text-gray-900">
                            관리자 대시보드
                        </h1>
                        
                        <div className="flex items-center space-x-4">
                            <select
                                value={refreshInterval}
                                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                            >
                                <option value={10}>10초마다 새로고침</option>
                                <option value={30}>30초마다 새로고침</option>
                                <option value={60}>1분마다 새로고침</option>
                                <option value={300}>5분마다 새로고침</option>
                            </select>
                            
                            <button
                                onClick={loadDashboardData}
                                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                            >
                                새로고침
                            </button>
                        </div>
                    </div>
                    
                    {/* 탭 네비게이션 */}
                    <div className="flex space-x-8">
                        {[
                            { id: 'overview', name: '개요' },
                            { id: 'users', name: '사용자 분석' },
                            { id: 'games', name: '게임 분석' },
                            { id: 'system', name: '시스템 상태' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                                    activeTab === tab.id
                                        ? 'border-blue-500 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                {tab.name}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* 메인 콘텐츠 */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {activeTab === 'overview' && (
                    <div className="space-y-8">
                        {/* 주요 메트릭 카드 */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <div className="bg-white rounded-lg shadow p-6">
                                <div className="flex items-center">
                                    <div className="flex-shrink-0">
                                        <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                                            <span className="text-white text-sm font-bold">👥</span>
                                        </div>
                                    </div>
                                    <div className="ml-5 w-0 flex-1">
                                        <dl>
                                            <dt className="text-sm font-medium text-gray-500 truncate">
                                                전체 사용자
                                            </dt>
                                            <dd className="text-lg font-medium text-gray-900">
                                                {formatNumber(dashboardData?.users?.total_users || 0)}
                                            </dd>
                                        </dl>
                                    </div>
                                </div>
                                <div className="mt-3">
                                    <div className="flex items-center text-sm">
                                        <span className="text-green-600 font-medium">
                                            +{dashboardData?.users?.new_users_today || 0}
                                        </span>
                                        <span className="text-gray-500 ml-1">오늘 신규</span>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white rounded-lg shadow p-6">
                                <div className="flex items-center">
                                    <div className="flex-shrink-0">
                                        <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                                            <span className="text-white text-sm font-bold">🟢</span>
                                        </div>
                                    </div>
                                    <div className="ml-5 w-0 flex-1">
                                        <dl>
                                            <dt className="text-sm font-medium text-gray-500 truncate">
                                                온라인 사용자
                                            </dt>
                                            <dd className="text-lg font-medium text-gray-900">
                                                {formatNumber(dashboardData?.users?.online_users || 0)}
                                            </dd>
                                        </dl>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white rounded-lg shadow p-6">
                                <div className="flex items-center">
                                    <div className="flex-shrink-0">
                                        <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                                            <span className="text-white text-sm font-bold">🎮</span>
                                        </div>
                                    </div>
                                    <div className="ml-5 w-0 flex-1">
                                        <dl>
                                            <dt className="text-sm font-medium text-gray-500 truncate">
                                                진행 중인 게임
                                            </dt>
                                            <dd className="text-lg font-medium text-gray-900">
                                                {dashboardData?.games?.active_games || 0}
                                            </dd>
                                        </dl>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-white rounded-lg shadow p-6">
                                <div className="flex items-center">
                                    <div className="flex-shrink-0">
                                        <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                                            <span className="text-white text-sm font-bold">📊</span>
                                        </div>
                                    </div>
                                    <div className="ml-5 w-0 flex-1">
                                        <dl>
                                            <dt className="text-sm font-medium text-gray-500 truncate">
                                                오늘 게임 수
                                            </dt>
                                            <dd className="text-lg font-medium text-gray-900">
                                                {formatNumber(dashboardData?.games?.games_today || 0)}
                                            </dd>
                                        </dl>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 시스템 상태 */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="px-6 py-4 border-b border-gray-200">
                                <h3 className="text-lg font-medium text-gray-900">시스템 상태</h3>
                            </div>
                            <div className="p-6">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-500">데이터베이스</span>
                                            <span className={`text-sm font-medium ${getStatusColor(dashboardData?.system?.database?.status)}`}>
                                                {dashboardData?.system?.database?.status === 'healthy' ? '정상' : '오류'}
                                            </span>
                                        </div>
                                        <div className="mt-1 text-xs text-gray-400">
                                            응답시간: {dashboardData?.system?.database?.response_time_ms || 0}ms
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-500">Redis</span>
                                            <span className={`text-sm font-medium ${getStatusColor(dashboardData?.system?.redis?.status)}`}>
                                                {dashboardData?.system?.redis?.status === 'healthy' ? '정상' : '오류'}
                                            </span>
                                        </div>
                                        <div className="mt-1 text-xs text-gray-400">
                                            응답시간: {dashboardData?.system?.redis?.response_time_ms || 0}ms
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-500">CPU 사용률</span>
                                            <span className="text-sm font-medium text-gray-900">
                                                {(dashboardData?.system?.cpu_percent || 0).toFixed(1)}%
                                            </span>
                                        </div>
                                        <div className="mt-1">
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div 
                                                    className="bg-blue-600 h-2 rounded-full"
                                                    style={{ width: `${dashboardData?.system?.cpu_percent || 0}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 실시간 활동 */}
                        <RealtimeUpdates realtimeData={dashboardData?.real_time} />
                    </div>
                )}

                {activeTab === 'users' && (
                    <UserAnalyticsChart data={userAnalytics} />
                )}

                {activeTab === 'games' && (
                    <GameAnalyticsChart data={gameAnalytics} />
                )}

                {activeTab === 'system' && (
                    <SystemHealthPanel systemData={dashboardData?.system} />
                )}
            </div>
        </div>
    );
};

export default AdminDashboard;
```

---

## 구현 우선순위

### Phase 1 (2주차): 기본 대시보드
1. **기본 메트릭 수집** - 사용자, 게임, 시스템 통계
2. **실시간 모니터링** - WebSocket 기반 실시간 업데이트
3. **어드민 인증** - 관리자 로그인 및 권한 시스템

### Phase 2 (1주차): 사용자 관리
1. **사용자 목록 및 검색** - 전체 사용자 조회 기능
2. **계정 관리** - 정지, 차단, 활성화 기능
3. **활동 로그** - 사용자 행동 추적

### Phase 3 (1주차): 고급 분석
1. **상세 분석 차트** - Chart.js 기반 시각화
2. **성능 모니터링** - API 응답시간, 에러율 추적
3. **보고서 생성** - PDF/Excel 내보내기

이 가이드를 통해 KKUA의 효율적인 운영과 관리를 위한 완전한 어드민 시스템을 구축할 수 있습니다.