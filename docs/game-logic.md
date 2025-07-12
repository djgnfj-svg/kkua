# 게임 로직 문서

## 끝말잇기 게임 규칙

### 기본 규칙
1. **순서대로 진행**: 참가자들이 정해진 순서대로 단어를 입력
2. **끝말잇기**: 이전 단어의 마지막 글자로 시작하는 단어 입력
3. **제한시간**: 각 턴마다 정해진 시간 내에 단어 입력 (기본 30초)
4. **중복 금지**: 이미 사용된 단어는 재사용 불가
5. **유효 단어**: 한글 단어만 허용 (2글자 이상)

### 승리 조건
- **생존형**: 마지막까지 남은 플레이어 승리
- **점수형**: 제한 시간 내에 가장 높은 점수를 획득한 플레이어 승리
- **라운드형**: 정해진 라운드를 완주한 플레이어 중 최고 점수자 승리

### 점수 계산
- **기본 점수**: 글자 수 × 1점
- **보너스 점수**: 
  - 긴 단어 (5글자 이상): +2점
  - 빠른 입력 (5초 이내): +1점
  - 특수 글자 (ㅢ, ㅟ 등): +3점

## 게임 상태 관리

### WordChainGameEngine

```python
@dataclass
class GameState:
    """게임 상태를 나타내는 데이터 클래스"""
    current_player_id: Optional[int] = None
    last_word: Optional[str] = None
    last_character: Optional[str] = None
    used_words: List[str] = field(default_factory=list)
    players: List[int] = field(default_factory=list)
    round_number: int = 0
    game_status: str = "waiting"  # waiting, playing, finished
    turn_start_time: Optional[float] = None
    time_limit: int = 30  # 초
    scores: Dict[int, int] = field(default_factory=dict)

class WordChainGameEngine:
    """끝말잇기 게임의 로직을 관리하는 클래스"""
    
    def __init__(self):
        self.game_states: Dict[int, GameState] = {}  # room_id -> GameState
        self.word_validator = WordValidator()
        self.score_calculator = ScoreCalculator()
```

### 게임 초기화

```python
def start_game(self, room_id: int, players: List[int]) -> GameState:
    """게임을 시작하고 초기 상태를 설정"""
    game_state = GameState(
        players=players.copy(),
        current_player_id=players[0] if players else None,
        game_status="playing",
        turn_start_time=time.time(),
        scores={player_id: 0 for player_id in players}
    )
    
    self.game_states[room_id] = game_state
    return game_state
```

### 단어 제출 처리

```python
async def handle_word_submission(self, room_id: int, player_id: int, word: str) -> dict:
    """플레이어의 단어 제출을 처리"""
    game_state = self.game_states.get(room_id)
    if not game_state:
        return {"valid": False, "message": "게임이 진행 중이 아닙니다"}
    
    # 1. 턴 검증
    if game_state.current_player_id != player_id:
        return {"valid": False, "message": "당신의 차례가 아닙니다"}
    
    # 2. 시간 검증
    if self._is_time_exceeded(game_state):
        await self._handle_timeout(room_id, player_id)
        return {"valid": False, "message": "시간이 초과되었습니다"}
    
    # 3. 단어 검증
    validation_result = self.word_validator.validate_word(
        word, game_state.last_character, game_state.used_words
    )
    
    if not validation_result.valid:
        await self._handle_invalid_word(room_id, player_id, validation_result.message)
        return {"valid": False, "message": validation_result.message}
    
    # 4. 유효한 단어 처리
    response_time = time.time() - game_state.turn_start_time
    score = self.score_calculator.calculate_score(word, response_time)
    
    # 게임 상태 업데이트
    game_state.last_word = word
    game_state.last_character = word[-1]
    game_state.used_words.append(word)
    game_state.scores[player_id] += score
    game_state.round_number += 1
    
    # 다음 플레이어로 턴 변경
    self._advance_turn(game_state)
    
    # 게임 종료 조건 확인
    if self._check_game_end_conditions(game_state):
        await self._end_game(room_id)
    
    return {
        "valid": True,
        "word": word,
        "score": score,
        "total_score": game_state.scores[player_id],
        "next_player": game_state.current_player_id,
        "last_character": game_state.last_character,
        "message": f"'{word}' 단어가 승인되었습니다 (+{score}점)"
    }
```

## 단어 검증 시스템

### WordValidator 클래스

```python
@dataclass
class ValidationResult:
    valid: bool
    message: str
    suggestion: Optional[str] = None

class WordValidator:
    """단어 유효성 검증을 담당하는 클래스"""
    
    def __init__(self):
        self.korean_dict = KoreanDictionary()  # 한국어 사전
        self.prohibited_words = self._load_prohibited_words()
    
    def validate_word(self, word: str, required_start_char: Optional[str], 
                     used_words: List[str]) -> ValidationResult:
        """종합적인 단어 검증"""
        
        # 1. 기본 형식 검증
        if not self._is_valid_format(word):
            return ValidationResult(False, "한글 2글자 이상만 입력 가능합니다")
        
        # 2. 중복 검증
        if word in used_words:
            return ValidationResult(False, f"'{word}'은(는) 이미 사용된 단어입니다")
        
        # 3. 끝말잇기 규칙 검증
        if required_start_char and word[0] != required_start_char:
            return ValidationResult(
                False, 
                f"'{required_start_char}'(으)로 시작하는 단어를 입력해주세요"
            )
        
        # 4. 금지 단어 검증
        if word in self.prohibited_words:
            return ValidationResult(False, "사용할 수 없는 단어입니다")
        
        # 5. 사전 검증
        if not self.korean_dict.is_valid_word(word):
            suggestion = self.korean_dict.get_similar_word(word)
            return ValidationResult(
                False, 
                f"'{word}'은(는) 사전에 없는 단어입니다",
                suggestion
            )
        
        # 6. 게임 종료 단어 검증 (ㄴ, ㄹ로 끝나는 단어)
        if self._is_game_ending_word(word):
            return ValidationResult(False, f"'{word[-1]}'로 끝나는 단어는 사용할 수 없습니다")
        
        return ValidationResult(True, "유효한 단어입니다")
    
    def _is_valid_format(self, word: str) -> bool:
        """기본 형식 검증: 한글 2글자 이상"""
        if len(word) < 2:
            return False
        return all('가' <= char <= '힣' for char in word)
    
    def _is_game_ending_word(self, word: str) -> bool:
        """게임 종료 문자로 끝나는지 확인"""
        ending_chars = ['ㄴ', 'ㄹ', 'ㅁ']  # 설정 가능한 게임 종료 문자들
        last_char_jamo = self._get_final_jamo(word[-1])
        return last_char_jamo in ending_chars
    
    def _get_final_jamo(self, char: str) -> str:
        """한글 문자의 종성 자모 추출"""
        if not ('가' <= char <= '힣'):
            return ''
        
        code = ord(char) - ord('가')
        final_jamo_index = code % 28
        
        if final_jamo_index == 0:
            return ''  # 받침 없음
        
        final_jamos = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        return final_jamos[final_jamo_index]
```

## 점수 계산 시스템

### ScoreCalculator 클래스

```python
class ScoreCalculator:
    """점수 계산을 담당하는 클래스"""
    
    def __init__(self):
        self.base_score = 1  # 글자당 기본 점수
        self.bonus_rules = BonusRules()
    
    def calculate_score(self, word: str, response_time: float) -> int:
        """단어와 응답 시간을 기반으로 점수 계산"""
        base_score = len(word) * self.base_score
        bonus_score = 0
        
        # 길이 보너스
        if len(word) >= 5:
            bonus_score += 2
        elif len(word) >= 7:
            bonus_score += 5
        
        # 속도 보너스
        if response_time <= 5:
            bonus_score += 3
        elif response_time <= 10:
            bonus_score += 1
        
        # 특수 문자 보너스
        bonus_score += self._calculate_special_char_bonus(word)
        
        # 희귀 단어 보너스
        if self._is_rare_word(word):
            bonus_score += 5
        
        return base_score + bonus_score
    
    def _calculate_special_char_bonus(self, word: str) -> int:
        """특수 한글 자모에 대한 보너스"""
        special_chars = {
            'ㅢ': 3, 'ㅟ': 3, 'ㅞ': 2, 'ㅝ': 2,
            'ㅚ': 2, 'ㅙ': 2, 'ㅘ': 1
        }
        
        bonus = 0
        for char in word:
            # 복합 모음 확인
            jungseong = self._get_jungseong(char)
            if jungseong in special_chars:
                bonus += special_chars[jungseong]
        
        return bonus
    
    def _is_rare_word(self, word: str) -> bool:
        """희귀 단어 여부 확인 (사용 빈도 기반)"""
        # 실제 구현에서는 단어 사용 통계 DB 조회
        rare_words = ['곤충학', '천체물리학', '양자역학', '생화학']
        return word in rare_words
```

## 게임 진행 플로우

### 1. 게임 시작

```python
async def start_game_flow(self, room_id: int, participants: List[GameroomParticipant]):
    """게임 시작 플로우"""
    
    # 1. 플레이어 목록 생성
    players = [p.guest_id for p in participants]
    random.shuffle(players)  # 순서 랜덤화
    
    # 2. 게임 상태 초기화
    game_state = self.start_game(room_id, players)
    
    # 3. 시작 메시지 브로드캐스트
    await self.connection_manager.broadcast_to_room(room_id, {
        "type": "game_started",
        "players": players,
        "current_player": game_state.current_player_id,
        "time_limit": game_state.time_limit,
        "message": "게임이 시작되었습니다!"
    })
    
    # 4. 첫 번째 플레이어에게 턴 알림
    await self._notify_current_player(room_id, game_state.current_player_id)
```

### 2. 턴 진행

```python
async def _advance_turn(self, game_state: GameState):
    """다음 플레이어로 턴 변경"""
    current_index = game_state.players.index(game_state.current_player_id)
    next_index = (current_index + 1) % len(game_state.players)
    
    game_state.current_player_id = game_state.players[next_index]
    game_state.turn_start_time = time.time()

async def _notify_current_player(self, room_id: int, player_id: int):
    """현재 플레이어에게 턴 알림"""
    await self.connection_manager.broadcast_to_room(room_id, {
        "type": "turn_changed",
        "current_player": player_id,
        "last_character": self.game_states[room_id].last_character,
        "time_limit": self.game_states[room_id].time_limit,
        "message": f"플레이어 {player_id}님의 차례입니다"
    })
```

### 3. 타임아웃 처리

```python
async def _handle_timeout(self, room_id: int, player_id: int):
    """시간 초과 처리"""
    game_state = self.game_states[room_id]
    
    # 타임아웃 페널티 적용
    penalty = 2
    game_state.scores[player_id] = max(0, game_state.scores[player_id] - penalty)
    
    # 플레이어 제거 (설정에 따라)
    if self._should_eliminate_on_timeout():
        game_state.players.remove(player_id)
        
        # 남은 플레이어가 1명 이하면 게임 종료
        if len(game_state.players) <= 1:
            await self._end_game(room_id)
            return
    
    # 다음 턴으로 이동
    self._advance_turn(game_state)
    
    await self.connection_manager.broadcast_to_room(room_id, {
        "type": "timeout",
        "timed_out_player": player_id,
        "penalty": penalty,
        "current_player": game_state.current_player_id,
        "message": f"플레이어 {player_id}님이 시간 초과되었습니다 (-{penalty}점)"
    })
```

### 4. 게임 종료

```python
async def _end_game(self, room_id: int):
    """게임 종료 처리"""
    game_state = self.game_states[room_id]
    game_state.game_status = "finished"
    
    # 최종 점수 계산 및 순위 결정
    final_scores = self._calculate_final_scores(game_state)
    winner = self._determine_winner(final_scores)
    
    # 게임 결과를 데이터베이스에 저장
    await self._save_game_result(room_id, game_state, final_scores, winner)
    
    # 결과 브로드캐스트
    await self.connection_manager.broadcast_to_room(room_id, {
        "type": "game_ended",
        "winner": winner,
        "final_scores": final_scores,
        "total_rounds": game_state.round_number,
        "message": f"게임이 종료되었습니다! 승자: {winner}"
    })
    
    # 게임 상태 정리
    del self.game_states[room_id]

def _calculate_final_scores(self, game_state: GameState) -> Dict[int, dict]:
    """최종 점수 및 통계 계산"""
    final_scores = {}
    
    for player_id in game_state.players:
        player_words = [
            word for word, pid in zip(game_state.used_words, game_state.word_players)
            if pid == player_id
        ]
        
        final_scores[player_id] = {
            "score": game_state.scores[player_id],
            "words_count": len(player_words),
            "longest_word": max(player_words, key=len) if player_words else "",
            "average_word_length": sum(len(w) for w in player_words) / len(player_words) if player_words else 0
        }
    
    return final_scores

def _determine_winner(self, final_scores: Dict[int, dict]) -> int:
    """승자 결정"""
    return max(final_scores.keys(), key=lambda pid: final_scores[pid]["score"])
```

## 아이템 시스템 (확장 기능)

### 아이템 타입

```python
class ItemType(Enum):
    SKIP_TURN = "skip_turn"          # 상대방 턴 스킵
    EXTRA_TIME = "extra_time"        # 추가 시간 부여
    WORD_HINT = "word_hint"          # 단어 힌트 제공
    SCORE_DOUBLE = "score_double"    # 점수 2배
    STEAL_POINTS = "steal_points"    # 상대방 점수 뺏기
    REVERSE_ORDER = "reverse_order"  # 순서 뒤바꾸기

@dataclass
class GameItem:
    item_type: ItemType
    name: str
    description: str
    cost: int  # 사용에 필요한 점수
    cooldown: int  # 재사용 대기시간 (초)

class ItemManager:
    """게임 아이템 관리"""
    
    def __init__(self):
        self.items = self._initialize_items()
        self.player_items = {}  # player_id -> List[ItemType]
        self.cooldowns = {}     # (player_id, item_type) -> end_time
    
    def use_item(self, player_id: int, item_type: ItemType, 
                game_state: GameState) -> dict:
        """아이템 사용"""
        
        # 아이템 보유 확인
        if not self._has_item(player_id, item_type):
            return {"success": False, "message": "아이템을 보유하고 있지 않습니다"}
        
        # 쿨다운 확인
        if self._is_on_cooldown(player_id, item_type):
            return {"success": False, "message": "아이템이 쿨다운 중입니다"}
        
        # 아이템 효과 적용
        effect_result = self._apply_item_effect(item_type, player_id, game_state)
        
        if effect_result["success"]:
            # 아이템 소모 및 쿨다운 적용
            self._consume_item(player_id, item_type)
            self._set_cooldown(player_id, item_type)
        
        return effect_result
```

## 난이도 조절

### 동적 난이도 조절

```python
class DifficultyManager:
    """게임 난이도 동적 조절"""
    
    def adjust_difficulty(self, game_state: GameState, player_stats: dict):
        """플레이어 실력에 따른 난이도 조절"""
        
        avg_response_time = self._calculate_avg_response_time(player_stats)
        avg_score = self._calculate_avg_score(player_stats)
        
        # 숙련자 그룹인 경우
        if avg_response_time < 10 and avg_score > 50:
            game_state.time_limit = max(15, game_state.time_limit - 5)
            self._enable_hard_mode_rules(game_state)
        
        # 초보자 그룹인 경우
        elif avg_response_time > 20 or avg_score < 20:
            game_state.time_limit = min(60, game_state.time_limit + 10)
            self._enable_easy_mode_rules(game_state)
    
    def _enable_hard_mode_rules(self, game_state: GameState):
        """어려운 모드 규칙 적용"""
        # 3글자 이상만 허용
        game_state.min_word_length = 3
        # 특수 종성 단어 허용
        game_state.allow_special_endings = False
    
    def _enable_easy_mode_rules(self, game_state: GameState):
        """쉬운 모드 규칙 적용"""
        # 2글자도 허용
        game_state.min_word_length = 2
        # 힌트 제공
        game_state.provide_hints = True
```

이 게임 로직은 확장 가능하고 공정한 게임 환경을 제공하면서도 다양한 게임 모드와 기능을 지원할 수 있도록 설계되었습니다.