# KKUA 고급 기능 개발 로드맵

## 📊 현재 상태 분석

### ✅ 구현 완료된 핵심 기능
- **인증 시스템**: 세션 기반 인증, HTTP-only 쿠키 보안
- **게임 플로우**: 로그인 → 로비 → 게임 로비 → 실시간 게임 → 결과
- **실시간 통신**: WebSocket 기반 실시간 게임 상태 동기화
- **데이터 아키텍처**: PostgreSQL(영구 데이터) + Redis(실시간 상태)
- **기본 게임 로직**: 끝말잇기 규칙, 턴 관리, 점수 계산
- **UI/UX**: 반응형 디자인, 연결 상태 관리, 토스트 알림

### 📈 개선 가능 영역
- **게임 메커니즘**: 단순한 10점/글자 점수 시스템
- **플레이어 참여도**: 기본적인 게임 모드만 존재
- **소셜 기능**: 채팅 외 상호작용 부족
- **진행 시스템**: 플레이어 성장/발전 요소 없음
- **관리 기능**: 어드민 도구 및 분석 기능 부재

---

## 🎯 Phase 1: 핵심 게임 기능 강화 (우선순위: 높음)

### 1.1 고급 점수 시스템

#### 현재 상태
```python
# backend/services/redis_game_service.py 현재 점수 계산
score = len(word) * 10  # 단순한 글자 수 기반 점수
```

#### 개선된 점수 시스템
```python
class AdvancedScoreCalculator:
    def __init__(self):
        self.base_score_per_char = 10
        self.speed_bonus_threshold = 15  # 15초 이하 빠른 응답
        self.combo_multiplier = 1.2     # 연속 성공 시 20% 보너스
        self.rare_word_bonus = {
            'common': 1.0,      # 자주 사용되는 단어
            'uncommon': 1.5,    # 보통 단어
            'rare': 2.0,        # 희귀 단어
            'very_rare': 3.0    # 매우 희귀한 단어
        }
    
    def calculate_score(self, word: str, response_time: float, 
                       combo_count: int, difficulty_rating: str) -> int:
        """
        고급 점수 계산 알고리즘
        - 기본 점수: 글자 수 × 10
        - 속도 보너스: 빠른 응답 시 추가 점수
        - 콤보 보너스: 연속 성공 시 곱셈 보너스
        - 희귀도 보너스: 단어 사용 빈도에 따른 보너스
        """
        base_score = len(word) * self.base_score_per_char
        
        # 속도 보너스 (15초 이하 시 최대 50점 추가)
        speed_bonus = max(0, (self.speed_bonus_threshold - response_time) * 2)
        
        # 콤보 보너스 (연속 성공 시 누적)
        combo_bonus = base_score * (self.combo_multiplier ** combo_count - 1)
        
        # 희귀도 보너스
        rarity_multiplier = self.rare_word_bonus.get(difficulty_rating, 1.0)
        
        total_score = (base_score + speed_bonus + combo_bonus) * rarity_multiplier
        return int(total_score)
```

#### 구현 계획
1. **단어 희귀도 데이터베이스 구축**: 한국어 단어 사용 빈도 분석
2. **콤보 시스템 추가**: Redis에 플레이어별 연속 성공 카운터
3. **실시간 점수 표시**: 프론트엔드에 점수 계산 상세 정보 표시
4. **성취 시스템**: 높은 점수 달성 시 특별 효과

### 1.2 전략적 아이템 시스템

#### 아이템 종류 및 효과
```python
# backend/models/item_model.py
class Item(Base):
    __tablename__ = "items"
    
    item_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    effect_type = Column(String(30))  # skip_turn, extra_time, score_boost
    effect_value = Column(Integer)
    cost = Column(Integer)           # 구매 비용
    rarity = Column(String(20))      # common, rare, epic, legendary
    cooldown_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class PlayerInventory(Base):
    __tablename__ = "player_inventories"
    
    inventory_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"))
    item_id = Column(Integer, ForeignKey("items.item_id"))
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime, default=datetime.utcnow)
```

#### 아이템 효과 정의
```python
GAME_ITEMS = {
    "skip_turn": {
        "name": "턴 스킵",
        "description": "상대방의 턴을 건너뛰고 바로 내 턴으로 만듭니다",
        "cost": 15,
        "cooldown": 60,
        "rarity": "common",
        "effect": "skip_next_player_turn"
    },
    "extra_time": {
        "name": "시간 연장",
        "description": "현재 턴의 제한 시간을 15초 추가합니다",
        "cost": 20,
        "cooldown": 45,
        "rarity": "common",
        "effect": "add_turn_time:15"
    },
    "score_double": {
        "name": "점수 배수",
        "description": "다음 단어의 점수를 2배로 받습니다",
        "cost": 30,
        "cooldown": 120,
        "rarity": "rare",
        "effect": "next_word_score_multiplier:2"
    },
    "word_hint": {
        "name": "단어 힌트",
        "description": "사용 가능한 단어의 첫 글자 힌트를 제공합니다",
        "cost": 10,
        "cooldown": 30,
        "rarity": "common",
        "effect": "show_word_hint"
    },
    "steal_points": {
        "name": "점수 훔치기",
        "description": "가장 높은 점수 플레이어에게서 점수의 20%를 가져옵니다",
        "cost": 40,
        "cooldown": 180,
        "rarity": "epic",
        "effect": "steal_percentage:20"
    },
    "reverse_order": {
        "name": "순서 뒤바꾸기",
        "description": "플레이어 턴 순서를 반대로 바꿉니다",
        "cost": 25,
        "cooldown": 90,
        "rarity": "rare",
        "effect": "reverse_player_order"
    }
}
```

### 1.3 다양한 게임 모드

#### 게임 모드 설정
```python
# backend/models/gameroom_model.py 확장
class GameMode(str, Enum):
    CLASSIC = "classic"      # 기본 모드 (현재)
    BLITZ = "blitz"         # 빠른 게임 (15초 턴)
    MARATHON = "marathon"    # 긴 게임 (20라운드)
    SURVIVAL = "survival"    # 탈락제 게임
    TEAM_BATTLE = "team_battle"  # 팀 대전
    CHALLENGE = "challenge"  # 일일 챌린지

GAME_MODE_CONFIGS = {
    GameMode.CLASSIC: {
        "turn_time_limit": 30,
        "max_rounds": 10,
        "max_players": 6,
        "items_enabled": False,
        "lives_per_player": 0  # 무제한
    },
    GameMode.BLITZ: {
        "turn_time_limit": 15,
        "max_rounds": 8,
        "max_players": 4,
        "items_enabled": True,
        "lives_per_player": 0
    },
    GameMode.MARATHON: {
        "turn_time_limit": 45,
        "max_rounds": 20,
        "max_players": 8,
        "items_enabled": True,
        "lives_per_player": 0
    },
    GameMode.SURVIVAL: {
        "turn_time_limit": 20,
        "max_rounds": 0,  # 무제한
        "max_players": 6,
        "items_enabled": True,
        "lives_per_player": 3  # 3번 실패 시 탈락
    },
    GameMode.TEAM_BATTLE: {
        "turn_time_limit": 25,
        "max_rounds": 12,
        "max_players": 6,  # 3vs3
        "items_enabled": True,
        "lives_per_player": 0,
        "teams": 2
    }
}
```

---

## 🤝 Phase 2: 소셜 & 커뮤니티 기능 (우선순위: 중상)

### 2.1 친구 시스템

#### 데이터 모델
```python
# backend/models/friend_model.py
class Friend(Base):
    __tablename__ = "friends"
    
    friend_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("guests.guest_id"))
    friend_user_id = Column(Integer, ForeignKey("guests.guest_id"))
    status = Column(String(20), default="pending")  # pending, accepted, blocked
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime)

class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    
    profile_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), unique=True)
    display_name = Column(String(50))
    bio = Column(Text)
    avatar_url = Column(String(255))
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    total_score = Column(BigInteger, default=0)
    favorite_words = Column(JSON)  # 자주 사용하는 단어 목록
    achievements = Column(JSON)    # 획득한 업적 목록
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

#### API 엔드포인트
```python
# backend/routers/friend_router.py
@router.post("/friends/request")
async def send_friend_request(request: FriendRequestSchema, current_user: Guest = Depends(require_authentication)):
    """친구 요청 보내기"""
    
@router.get("/friends")
async def get_friends_list(current_user: Guest = Depends(require_authentication)):
    """친구 목록 조회"""
    
@router.post("/friends/{friend_id}/accept")
async def accept_friend_request(friend_id: int, current_user: Guest = Depends(require_authentication)):
    """친구 요청 수락"""

@router.get("/profiles/{user_id}")
async def get_player_profile(user_id: int):
    """플레이어 프로필 조회"""
```

### 2.2 토너먼트 시스템

#### 토너먼트 구조
```python
# backend/models/tournament_model.py
class Tournament(Base):
    __tablename__ = "tournaments"
    
    tournament_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    format = Column(String(30))  # single_elimination, double_elimination, round_robin
    max_participants = Column(Integer)
    entry_fee = Column(Integer, default=0)  # 가상 화폐 entry fee
    prize_pool = Column(Integer, default=0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(20), default="registration")  # registration, ongoing, completed
    created_by = Column(Integer, ForeignKey("guests.guest_id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    
    participant_id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.tournament_id"))
    guest_id = Column(Integer, ForeignKey("guests.guest_id"))
    seed = Column(Integer)  # 시드 번호
    current_round = Column(Integer, default=1)
    is_eliminated = Column(Boolean, default=False)
    final_rank = Column(Integer)
    registered_at = Column(DateTime, default=datetime.utcnow)

class TournamentMatch(Base):
    __tablename__ = "tournament_matches"
    
    match_id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.tournament_id"))
    round_number = Column(Integer)
    match_number = Column(Integer)
    player1_id = Column(Integer, ForeignKey("guests.guest_id"))
    player2_id = Column(Integer, ForeignKey("guests.guest_id"))
    winner_id = Column(Integer, ForeignKey("guests.guest_id"))
    game_room_id = Column(Integer, ForeignKey("gamerooms.room_id"))
    status = Column(String(20), default="pending")  # pending, ongoing, completed
    scheduled_time = Column(DateTime)
    completed_at = Column(DateTime)
```

---

## 📊 Phase 3: 분석 & 관리 기능 (우선순위: 중)

### 3.1 어드민 대시보드

#### 실시간 메트릭
```python
# backend/services/analytics_service.py
class AnalyticsService:
    def __init__(self, db: Session, redis_client):
        self.db = db
        self.redis = redis_client
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """실시간 시스템 메트릭"""
        return {
            "active_players": await self._count_active_players(),
            "ongoing_games": await self._count_ongoing_games(),
            "total_rooms": await self._count_total_rooms(),
            "server_performance": await self._get_server_metrics(),
            "redis_performance": await self._get_redis_metrics()
        }
    
    async def get_game_analytics(self, days: int = 7) -> Dict[str, Any]:
        """게임 분석 데이터"""
        return {
            "popular_words": await self._get_popular_words(days),
            "average_game_duration": await self._calculate_avg_duration(days),
            "player_retention": await self._calculate_retention_rate(days),
            "peak_hours": await self._analyze_usage_patterns(days),
            "score_distribution": await self._analyze_score_distribution(days)
        }
    
    async def get_player_insights(self) -> Dict[str, Any]:
        """플레이어 행동 분석"""
        return {
            "new_player_count": await self._count_new_players(7),
            "returning_player_rate": await self._calculate_return_rate(),
            "average_session_duration": await self._calculate_avg_session(),
            "most_active_players": await self._get_top_players(),
            "geographic_distribution": await self._analyze_player_locations()
        }
```

#### 어드민 대시보드 UI
```javascript
// frontend/src/Pages/Admin/AdminDashboard.js
const AdminDashboard = () => {
    const [metrics, setMetrics] = useState(null);
    const [gameAnalytics, setGameAnalytics] = useState(null);
    const [playerInsights, setPlayerInsights] = useState(null);
    
    // 실시간 메트릭 업데이트 (WebSocket)
    useEffect(() => {
        const ws = new WebSocket(`${WS_BASE_URL}/ws/admin/metrics`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_update') {
                setMetrics(data.metrics);
            }
        };
        return () => ws.close();
    }, []);
    
    return (
        <div className="admin-dashboard">
            <RealTimeMetrics metrics={metrics} />
            <GameAnalyticsCharts analytics={gameAnalytics} />
            <PlayerInsightsPanel insights={playerInsights} />
            <ModerationsTools />
        </div>
    );
};
```

### 3.2 성능 모니터링

#### 성능 메트릭 수집
```python
# backend/middleware/performance_middleware.py
class PerformanceMiddleware:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # WebSocket 연결 지연시간 측정
        if request.url.path.startswith("/ws/"):
            await self._measure_websocket_latency(request)
        
        response = await call_next(request)
        
        # API 응답 시간 측정
        process_time = time.time() - start_time
        await self._record_api_metrics(request, response, process_time)
        
        return response
    
    async def _record_api_metrics(self, request, response, duration):
        """API 메트릭 기록"""
        metrics = {
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "timestamp": datetime.utcnow()
        }
        await self.metrics_collector.record_api_call(metrics)
```

---

## 📱 Phase 4: 모바일 & 접근성 (우선순위: 중)

### 4.1 모바일 최적화

#### PWA 설정
```json
// frontend/public/manifest.json (확장)
{
  "name": "끄아 - KKUA 끝말잇기",
  "short_name": "KKUA",
  "description": "실시간 멀티플레이어 끝말잇기 게임",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a365d",
  "theme_color": "#2d3748",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "빠른 게임",
      "short_name": "빠른 게임",
      "description": "즉시 게임 참여",
      "url": "/quick-match",
      "icons": [{ "src": "/icons/quick-match.png", "sizes": "96x96" }]
    }
  ]
}
```

#### 터치 최적화 컴포넌트
```javascript
// frontend/src/components/mobile/VirtualKeyboard.js
const VirtualKeyboard = ({ onKeyPress, currentLastChar }) => {
    const koreanKeyboard = [
        ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ'],
        ['ㅋ', 'ㅌ', 'ㅍ', 'ㅎ', 'ㅏ', 'ㅑ', 'ㅓ', 'ㅕ', 'ㅗ', 'ㅛ'],
        ['ㅜ', 'ㅠ', 'ㅡ', 'ㅣ', 'ㅐ', 'ㅒ', 'ㅔ', 'ㅖ', 'ㅢ']
    ];
    
    // 마지막 글자에 따른 추천 자음 하이라이트
    const getRecommendedChars = (lastChar) => {
        // 받침에 따른 추천 시작 자음 계산
        return [];
    };
    
    return (
        <div className="virtual-keyboard fixed bottom-0 left-0 right-0 bg-gray-800 p-2">
            {/* 한글 자판 구현 */}
        </div>
    );
};
```

### 4.2 접근성 개선

#### 음성 입력 지원
```javascript
// frontend/src/hooks/useSpeechRecognition.js
const useSpeechRecognition = () => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    
    useEffect(() => {
        if (!('webkitSpeechRecognition' in window)) {
            console.warn('Speech recognition not supported');
            return;
        }
        
        const recognition = new window.webkitSpeechRecognition();
        recognition.lang = 'ko-KR';
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onresult = (event) => {
            const result = event.results[0][0].transcript;
            setTranscript(result);
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            setIsListening(false);
        };
        
        recognition.onend = () => {
            setIsListening(false);
        };
        
        if (isListening) {
            recognition.start();
        }
        
        return () => recognition.stop();
    }, [isListening]);
    
    return { isListening, transcript, startListening: () => setIsListening(true) };
};
```

---

## 🔗 구현 우선순위 및 의존성

### Phase 1 상세 구현 순서
1. **고급 점수 시스템** (1주) → 기존 시스템 확장
2. **아이템 시스템** (2주) → 새로운 데이터 모델 및 로직
3. **게임 모드 다양화** (1주) → 기존 게임 로직 확장

### Phase 2 상세 구현 순서
1. **친구 시스템** (1.5주) → 소셜 기능의 기반
2. **플레이어 프로필** (1주) → 친구 시스템과 연동
3. **토너먼트 시스템** (1.5주) → 경쟁 요소 추가

### Phase 3 상세 구현 순서
1. **기본 분석 도구** (1주) → 데이터 수집 시작
2. **어드민 대시보드** (1.5주) → 관리 기능
3. **성능 모니터링** (1주) → 시스템 최적화

### Phase 4 상세 구현 순서
1. **모바일 UI 최적화** (1주) → 기존 UI 개선
2. **PWA 기능** (0.5주) → 앱화
3. **접근성 기능** (1주) → 사용자 경험 개선

---

## 📈 성공 지표 및 KPI

### 사용자 참여도
- **평균 세션 시간**: 현재 15분 → 목표 25분
- **일일 활성 사용자**: 현재 수치 → 목표 60% 증가
- **게임 완료율**: 현재 70% → 목표 85%
- **재방문율**: 현재 수치 → 목표 40% 증가

### 기술적 성능
- **WebSocket 지연시간**: 100ms 이하 유지
- **게임 로딩 시간**: 3초 이하
- **동시 접속자**: 1000명 이상 지원
- **시스템 가동률**: 99.9% 이상

### 비즈니스 메트릭
- **신규 기능 사용률**: 출시 후 1개월 내 70% 이상
- **사용자 만족도**: 앱스토어 평점 4.5/5 이상
- **커뮤니티 활성도**: 친구 추가율 50% 이상
- **경쟁 참여율**: 토너먼트 참가율 30% 이상

이 로드맵을 통해 KKUA를 단순한 끝말잇기 게임에서 종합적인 멀티플레이어 게임 플랫폼으로 발전시킬 수 있습니다.