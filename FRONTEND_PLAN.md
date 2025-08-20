# 🎮 KKUA 프론트엔드 개발 기획서

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [기술 스택 결정](#기술-스택-결정)
3. [화면 구성 및 플로우](#화면-구성-및-플로우)
4. [핵심 기능 명세](#핵심-기능-명세)
5. [UI/UX 디자인 가이드](#uiux-디자인-가이드)
6. [컴포넌트 구조](#컴포넌트-구조)
7. [상태 관리 전략](#상태-관리-전략)
8. [WebSocket 통신 설계](#websocket-통신-설계)
9. [개발 로드맵](#개발-로드맵)
10. [테스트 전략](#테스트-전략)

---

## 🎯 프로젝트 개요

### 목표
실시간 멀티플레이어 한국어 끝말잇기 게임의 웹 클라이언트 개발

### 핵심 요구사항
- ✅ 실시간 WebSocket 통신
- ✅ 반응형 디자인 (PC/모바일)
- ✅ 직관적이고 재미있는 게임 UI
- ✅ 최소한의 로딩 시간
- ✅ 부드러운 애니메이션

### 타겟 사용자
- 주요: 10-30대 한국어 사용자
- 디바이스: PC(60%), 모바일(40%)
- 동시 접속: 최대 1000명

---

## 🛠 기술 스택 결정

### 핵심 스택
```javascript
{
  "framework": "React 18.2",
  "buildTool": "Vite 5.0",
  "language": "TypeScript 5.3",
  "styling": "TailwindCSS 3.4 + CSS Modules",
  "stateManagement": "Zustand 4.5",
  "routing": "React Router 6.20",
  "websocket": "Socket.io-client 4.7",
  "animation": "Framer Motion 11.0",
  "httpClient": "Axios + React Query 5.0",
  "notification": "React Hot Toast 2.4",
  "forms": "React Hook Form 7.48",
  "testing": "Playwright (E2E)"
}
```

### 선택 이유
- **React**: 풍부한 생태계, 실시간 업데이트에 적합
- **Vite**: 빠른 HMR, 최적화된 빌드
- **TypeScript**: 백엔드 API와 타입 공유
- **Zustand**: 간단한 상태 관리, 작은 번들 사이즈
- **TailwindCSS**: 빠른 프로토타이핑, 일관된 디자인

---

## 🖼 화면 구성 및 플로우

### 1. 화면 구조도
```
┌─────────────────────────────────────────┐
│             Landing Page                │
│         [게스트로 시작] [로그인]           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│            Main Lobby                   │
│  ┌──────────┐  ┌──────────────────┐     │
│  │ 프로필   │  │   게임방 목록      │     │
│  │ 통계     │  │  [방 만들기]      │     │
│  │ 설정     │  │  [빠른 매칭]      │     │
│  └──────────┘  └──────────────────┘     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           Game Room                     │
│  ┌─────────────────────────────┐        │
│  │     Player List (1-8)       │        │
│  └─────────────────────────────┘        │
│  ┌─────────────────────────────┐        │
│  │     Word Chain Display      │        │
│  │     현재: "사과 → 과일"       │        │
│  └─────────────────────────────┘        │
│  ┌─────────────────────────────┐        │
│  │    Timer: 25초              │        │
│  │    [단어 입력창]             │        │
│  │    [제출]                   │        │
│  └─────────────────────────────┘        │
│  ┌─────────────────────────────┐        │
│  │    Items (1-5 slots)        │        │
│  └─────────────────────────────┘        │
└─────────────────────────────────────────┘
```

### 2. 페이지별 상세

#### 2.1 랜딩 페이지 (`/`)
- **목적**: 첫 진입점, 빠른 게임 시작
- **구성요소**:
  - 게임 로고 & 타이틀
  - 게스트 로그인 (닉네임만 입력)
  - 소셜 로그인 옵션 (Phase 2)
  - 게임 방법 간단 설명

#### 2.2 메인 로비 (`/lobby`)
- **목적**: 게임방 선택 및 생성
- **구성요소**:
  - 실시간 게임방 목록 (WebSocket 업데이트)
  - 방 필터링 (게임 모드, 인원수, 상태)
  - 빠른 매칭 버튼
  - 방 만들기 모달
  - 사용자 프로필 카드

#### 2.3 게임룸 (`/game/:roomId`)
- **목적**: 실제 게임 진행
- **구성요소**:
  - 플레이어 목록 & 점수
  - 단어 체인 시각화
  - 타이머 (원형 프로그레스)
  - 단어 입력 필드
  - 아이템 슬롯 (5개)
  - 채팅창 (토글 가능)

#### 2.4 결과 화면 (`/result/:gameId`)
- **목적**: 게임 결과 표시
- **구성요소**:
  - 순위표
  - MVP 하이라이트
  - 게임 통계 (최장 단어, 최다 점수 등)
  - 다시하기 / 나가기 버튼

---

## 🎮 핵심 기능 명세

### 1. 실시간 기능 (WebSocket)
```typescript
interface RealtimeFeatures {
  // 게임방 관련
  roomList: '실시간 방 목록 업데이트';
  playerJoin: '플레이어 입장 알림';
  playerLeave: '플레이어 퇴장 알림';
  
  // 게임 진행
  gameStart: '게임 시작 신호';
  turnChange: '턴 변경 알림';
  wordSubmit: '단어 제출 & 검증 결과';
  timerUpdate: '타이머 동기화';
  
  // 아이템 & 효과
  itemUse: '아이템 사용 효과';
  scoreUpdate: '점수 실시간 업데이트';
  
  // 게임 종료
  gameEnd: '게임 종료 & 결과';
}
```

### 2. 단어 입력 시스템
- **한글 자동완성**: 자모 분리 기반 추천
- **실시간 검증**: 입력 중 유효성 표시
- **엔터키 제출**: 빠른 입력 지원
- **모바일 최적화**: 가상 키보드 대응

### 3. 타이머 시스템
- **서버 동기화**: 클라이언트-서버 시간 차이 보정
- **시각적 피드백**: 
  - 30초: 초록색
  - 10초: 노란색
  - 5초: 빨간색 + 진동/소리

### 4. 아이템 시스템
```typescript
interface ItemUI {
  display: '아이템 아이콘 & 쿨다운';
  activation: '드래그 앤 드롭 or 클릭';
  effects: '시각적 효과 애니메이션';
  targetSelection: '대상 선택 UI (필요시)';
}
```

### 5. 반응형 디자인
- **PC (1920x1080)**: 풀 레이아웃
- **태블릿 (768px)**: 2컬럼 레이아웃
- **모바일 (375px)**: 단일 컬럼, 터치 최적화

---

## 🎨 UI/UX 디자인 가이드

### 1. 디자인 원칙
- **Minimal & Clean**: 게임에 집중할 수 있는 깔끔한 UI
- **Playful**: 재미있지만 과하지 않은 애니메이션
- **Accessible**: 색맹 대응, 큰 터치 영역
- **Fast**: 즉각적인 피드백, 로딩 최소화

### 2. 색상 팔레트
```css
:root {
  /* Primary Colors */
  --primary-500: #6366F1;  /* Indigo - 메인 액션 */
  --primary-600: #4F46E5;  /* Hover 상태 */
  
  /* Game States */
  --success: #10B981;      /* 정답, 성공 */
  --warning: #F59E0B;      /* 경고, 시간 부족 */
  --danger: #EF4444;       /* 오답, 타임아웃 */
  
  /* Neutral */
  --gray-50: #F9FAFB;      /* 배경 */
  --gray-900: #111827;     /* 텍스트 */
  
  /* Dark Mode (Phase 2) */
  --dark-bg: #1F2937;
  --dark-surface: #374151;
}
```

### 3. 타이포그래피
```css
/* 폰트: Pretendard (한글), Inter (영문) */
.heading-1 { @apply text-4xl font-bold; }
.heading-2 { @apply text-2xl font-semibold; }
.body { @apply text-base; }
.caption { @apply text-sm text-gray-600; }
```

### 4. 컴포넌트 스타일
- **버튼**: 둥근 모서리, 그림자, 호버 효과
- **카드**: 흰 배경, 얇은 테두리, 약간의 그림자
- **입력창**: 큰 패딩, 명확한 포커스 상태
- **모달**: 반투명 배경, 중앙 정렬, 슬라이드 애니메이션

---

## 🏗 컴포넌트 구조

### 1. 컴포넌트 계층
```
src/
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # 상단 네비게이션
│   │   ├── Footer.tsx          # 하단 정보
│   │   └── Container.tsx       # 레이아웃 컨테이너
│   │
│   ├── game/
│   │   ├── GameBoard.tsx       # 게임 보드 전체
│   │   ├── WordChain.tsx       # 단어 체인 표시
│   │   ├── WordInput.tsx       # 단어 입력 컴포넌트
│   │   ├── Timer.tsx           # 타이머 컴포넌트
│   │   ├── PlayerCard.tsx      # 플레이어 정보 카드
│   │   ├── ScoreBoard.tsx      # 점수판
│   │   └── ItemSlot.tsx        # 아이템 슬롯
│   │
│   ├── lobby/
│   │   ├── RoomList.tsx        # 방 목록
│   │   ├── RoomCard.tsx        # 방 카드
│   │   ├── CreateRoomModal.tsx # 방 만들기 모달
│   │   └── QuickMatch.tsx      # 빠른 매칭
│   │
│   └── ui/
│       ├── Button.tsx           # 범용 버튼
│       ├── Input.tsx            # 입력 필드
│       ├── Modal.tsx            # 모달
│       ├── Card.tsx             # 카드 컨테이너
│       ├── Badge.tsx            # 배지/태그
│       ├── Toast.tsx            # 토스트 알림
│       └── Loading.tsx          # 로딩 스피너
```

### 2. 핵심 컴포넌트 명세

#### WordInput 컴포넌트
```typescript
interface WordInputProps {
  onSubmit: (word: string) => void;
  disabled: boolean;
  placeholder?: string;
  lastChar?: string;  // 끝말잇기 마지막 글자
}

// 기능:
// - 한글만 입력 가능
// - 엔터키 제출
// - 자동완성 제안 (선택적)
// - 입력 중 실시간 검증
```

#### Timer 컴포넌트
```typescript
interface TimerProps {
  duration: number;      // 총 시간 (초)
  remaining: number;     // 남은 시간 (초)
  isMyTurn: boolean;     // 내 턴 여부
  onTimeout: () => void;
}

// 기능:
// - 원형 프로그레스 바
// - 색상 변화 (초록 → 노란 → 빨강)
// - 카운트다운 소리 (5초 이하)
```

---

## 📊 상태 관리 전략

### 1. Zustand Store 구조
```typescript
// stores/gameStore.ts
interface GameStore {
  // 게임 상태
  roomId: string | null;
  gamePhase: 'waiting' | 'playing' | 'finished';
  players: Player[];
  currentTurn: number;
  wordChain: Word[];
  
  // 액션
  joinRoom: (roomId: string) => void;
  submitWord: (word: string) => void;
  useItem: (itemId: number) => void;
}

// stores/userStore.ts
interface UserStore {
  // 사용자 정보
  userId: number | null;
  nickname: string;
  isGuest: boolean;
  stats: UserStats;
  
  // 인증
  login: (nickname: string) => Promise<void>;
  logout: () => void;
}

// stores/uiStore.ts
interface UIStore {
  // UI 상태
  isLoading: boolean;
  modal: ModalType | null;
  toast: ToastMessage | null;
  
  // UI 액션
  showModal: (type: ModalType) => void;
  showToast: (message: string, type: 'success' | 'error') => void;
}
```

### 2. 상태 동기화 전략
- **Optimistic Updates**: 단어 제출 시 즉시 UI 업데이트
- **Server Reconciliation**: 서버 응답으로 최종 상태 확정
- **Error Recovery**: 실패 시 이전 상태로 롤백

---

## 🔌 WebSocket 통신 설계

### 1. 연결 관리
```typescript
class WebSocketManager {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect(url: string, token: string) {
    this.socket = io(url, {
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });
    
    this.setupEventHandlers();
  }
  
  private setupEventHandlers() {
    // 연결 이벤트
    this.socket.on('connect', this.onConnect);
    this.socket.on('disconnect', this.onDisconnect);
    
    // 게임 이벤트
    this.socket.on('game:start', this.onGameStart);
    this.socket.on('game:update', this.onGameUpdate);
    this.socket.on('game:end', this.onGameEnd);
  }
}
```

### 2. 메시지 프로토콜
```typescript
// 클라이언트 → 서버
interface ClientMessage {
  type: 'join_room' | 'submit_word' | 'use_item' | 'chat';
  payload: any;
  timestamp: number;
}

// 서버 → 클라이언트
interface ServerMessage {
  type: 'room_update' | 'game_state' | 'word_result' | 'error';
  payload: any;
  timestamp: number;
}
```

### 3. 에러 처리 & 재연결
- **Exponential Backoff**: 재연결 시도 간격 증가
- **Message Queue**: 연결 끊김 시 메시지 큐잉
- **State Recovery**: 재연결 후 상태 동기화

---

## 📅 개발 로드맵

### Phase 1: 기초 구축
**목표: 프로젝트 기반 설정 및 기본 UI 시스템 구축**

#### 환경 설정
- [ ] Vite + React + TypeScript 프로젝트 생성
- [ ] ESLint + Prettier 설정
- [ ] 절대 경로 import 설정 (`@/components`)
- [ ] 환경 변수 설정 (.env)

#### 스타일링 시스템
- [ ] TailwindCSS 설치 및 설정
- [ ] 커스텀 테마 설정 (색상, 폰트, 간격)
- [ ] CSS 변수 정의 (다크모드 대비)
- [ ] 글로벌 스타일 설정

#### 라우팅 구조
- [ ] React Router 설치 및 설정
- [ ] 페이지 컴포넌트 구조 생성
- [ ] 404 페이지 구현
- [ ] 레이아웃 컴포넌트 구현

#### UI 컴포넌트 라이브러리
- [ ] Button 컴포넌트 (variants: primary, secondary, danger)
- [ ] Input 컴포넌트 (text, password, with validation)
- [ ] Card 컴포넌트
- [ ] Modal 컴포넌트
- [ ] Loading 스피너
- [ ] Toast 알림 시스템

### Phase 2: 핵심 기능 구현
**목표: 게임의 핵심 기능 및 통신 시스템 구축**

#### WebSocket 통신 시스템
- [ ] Socket.io-client 설치 및 설정
- [ ] WebSocket Hook 구현 (`useWebSocket`)
- [ ] 자동 재연결 로직 구현
- [ ] 메시지 큐 시스템
- [ ] 연결 상태 관리
- [ ] 에러 핸들링

#### 상태 관리
- [ ] Zustand 설치 및 설정
- [ ] userStore 구현 (사용자 정보, 인증)
- [ ] gameStore 구현 (게임 상태, 플레이어)
- [ ] uiStore 구현 (UI 상태, 모달, 토스트)

#### 인증 시스템
- [ ] 게스트 로그인 구현
- [ ] 세션 관리
- [ ] 자동 로그인 (localStorage)
- [ ] 로그아웃 기능

#### 로비 시스템
- [ ] 방 목록 실시간 조회
- [ ] 방 생성 모달 및 API
- [ ] 방 참가 기능
- [ ] 빠른 매칭 기능
- [ ] 방 필터링 (상태, 인원, 모드)

### Phase 3: 게임 플레이 구현
**목표: 실제 게임 진행에 필요한 모든 기능 구현**

#### 게임룸 UI
- [ ] 플레이어 목록 컴포넌트
- [ ] 점수판 컴포넌트
- [ ] 단어 체인 디스플레이
- [ ] 게임 상태 표시 (대기/진행/종료)

#### 단어 입력 시스템
- [ ] 한글 전용 입력 필드
- [ ] 실시간 유효성 검사
- [ ] 엔터키 제출
- [ ] 입력 비활성화 (다른 플레이어 턴)
- [ ] 마지막 글자 하이라이트

#### 타이머 시스템
- [ ] 원형 프로그레스 타이머
- [ ] 서버 시간 동기화
- [ ] 색상 변화 (30초→10초→5초)
- [ ] 카운트다운 효과음
- [ ] 타임아웃 처리

#### 실시간 게임 동기화
- [ ] 턴 변경 처리
- [ ] 단어 제출 결과 처리
- [ ] 점수 업데이트
- [ ] 플레이어 상태 업데이트
- [ ] 게임 종료 처리

#### 아이템 시스템
- [ ] 아이템 슬롯 UI (5개)
- [ ] 아이템 사용 인터페이스
- [ ] 아이템 효과 애니메이션
- [ ] 쿨다운 표시
- [ ] 대상 선택 UI

### Phase 4: 완성도 및 최적화
**목표: 사용자 경험 향상 및 안정성 확보**

#### 애니메이션 & 트랜지션
- [ ] Framer Motion 설치
- [ ] 페이지 전환 애니메이션
- [ ] 컴포넌트 등장 애니메이션
- [ ] 점수 증가 애니메이션
- [ ] 아이템 사용 효과

#### 반응형 디자인
- [ ] 모바일 레이아웃 (375px)
- [ ] 태블릿 레이아웃 (768px)
- [ ] 데스크톱 레이아웃 (1920px)
- [ ] 터치 제스처 지원
- [ ] 가상 키보드 대응

#### 에러 처리 & 복구
- [ ] 전역 에러 바운더리
- [ ] API 에러 처리
- [ ] WebSocket 에러 처리
- [ ] 사용자 친화적 에러 메시지
- [ ] 재시도 메커니즘

#### 성능 최적화
- [ ] 컴포넌트 메모이제이션
- [ ] 이미지 최적화
- [ ] 번들 사이즈 분석
- [ ] Code Splitting
- [ ] Lazy Loading

#### 사용자 경험
- [ ] 로딩 상태 표시
- [ ] 스켈레톤 UI
- [ ] 툴팁 & 가이드
- [ ] 키보드 단축키
- [ ] 효과음 시스템

### Phase 5: 테스트 및 배포
**목표: 품질 보증 및 프로덕션 배포**

#### Playwright E2E 테스트
- [ ] 테스트 환경 설정
- [ ] 로그인 플로우 테스트
- [ ] 방 생성/참가 테스트
- [ ] 전체 게임 플로우 테스트
- [ ] 에러 시나리오 테스트
- [ ] 멀티 플레이어 시뮬레이션

#### 빌드 & 최적화
- [ ] 프로덕션 빌드 설정
- [ ] 환경 변수 분리
- [ ] 소스맵 설정
- [ ] 압축 설정
- [ ] CDN 설정

#### 배포
- [ ] Docker 설정 (선택)
- [ ] CI/CD 파이프라인
- [ ] 도메인 연결
- [ ] SSL 인증서
- [ ] 모니터링 설정

---

## 🧪 테스트 전략

### 1. Playwright E2E 테스트
```typescript
// tests/game-flow.spec.ts
test('전체 게임 플로우', async ({ page }) => {
  // 1. 랜딩 페이지 접속
  await page.goto('/');
  
  // 2. 게스트 로그인
  await page.fill('[data-testid="nickname-input"]', '테스트유저');
  await page.click('[data-testid="guest-login-btn"]');
  
  // 3. 방 생성
  await page.click('[data-testid="create-room-btn"]');
  
  // 4. 게임 시작
  await page.click('[data-testid="start-game-btn"]');
  
  // 5. 단어 입력
  await page.fill('[data-testid="word-input"]', '사과');
  await page.press('[data-testid="word-input"]', 'Enter');
  
  // 검증
  await expect(page.locator('.word-chain')).toContainText('사과');
});
```

### 2. 테스트 시나리오
- **기본 플로우**: 로그인 → 방 입장 → 게임 → 종료
- **에러 케이스**: 네트워크 끊김, 잘못된 입력
- **동시성**: 여러 플레이어 동시 액션
- **성능**: 대량 메시지 처리

---

## 📦 빌드 & 배포

### 1. 환경 변수
```env
# .env.development
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# .env.production
VITE_API_URL=https://api.kkua.game
VITE_WS_URL=wss://api.kkua.game/ws
```

### 2. 빌드 최적화
- **Code Splitting**: 라우트별 lazy loading
- **Tree Shaking**: 사용하지 않는 코드 제거
- **Asset Optimization**: 이미지/폰트 최적화
- **PWA**: 오프라인 지원 (선택적)

### 3. 배포 옵션
- **Vercel**: Next.js 최적화, 무료 티어
- **Netlify**: 간단한 배포, PR 프리뷰
- **Docker**: 백엔드와 통합 배포
- **CDN**: CloudFlare 정적 자산 캐싱

---

## 🎯 성공 지표

### 기술적 지표
- **First Contentful Paint**: < 1.5초
- **Time to Interactive**: < 3초
- **WebSocket 재연결**: < 2초
- **번들 사이즈**: < 500KB (gzipped)

### 사용자 경험 지표
- **게임 참여율**: 방문자 대비 80%
- **평균 세션 시간**: > 10분
- **재방문율**: > 30%
- **에러율**: < 1%

---

## 📝 참고사항

### 주의사항
1. **한글 입력**: IME 이슈 처리 필요
2. **모바일**: 가상 키보드 레이아웃 대응
3. **브라우저 호환성**: Chrome, Safari, Firefox 최신 2개 버전
4. **보안**: XSS, CSRF 방어

### 향후 계획 (Phase 2)
- 소셜 로그인 (Google, Kakao)
- 친구 시스템
- 리플레이 기능
- 다크 모드
- PWA 전환
- 다국어 지원

---

이 기획서를 기반으로 체계적인 프론트엔드 개발을 진행합니다.