-- 끄아(KKUA) V2 데이터베이스 스키마

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nickname VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    total_games INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_score BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

-- 게임 룸 테이블
CREATE TABLE IF NOT EXISTS game_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    max_players INTEGER DEFAULT 4,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'waiting', -- waiting, playing, finished
    settings JSONB DEFAULT '{}'
);

-- 게임 세션 테이블
CREATE TABLE IF NOT EXISTS game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES game_rooms(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    winner_id INTEGER REFERENCES users(id),
    total_rounds INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    duration_ms BIGINT,
    game_data JSONB, -- 게임 상세 데이터
    final_scores JSONB -- 최종 점수 정보
);

-- 한국어 사전 테이블
CREATE TABLE IF NOT EXISTS korean_dictionary (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) UNIQUE NOT NULL,
    definition TEXT,
    difficulty_level INTEGER DEFAULT 1, -- 1: 쉬움, 2: 보통, 3: 어려움
    frequency_score INTEGER DEFAULT 0,  -- 사용 빈도
    word_type VARCHAR(20), -- 명사, 동사, 형용사 등
    first_char CHAR(1) NOT NULL,
    last_char CHAR(1) NOT NULL,
    word_length INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 아이템 정의 테이블
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    rarity VARCHAR(20) NOT NULL, -- common, uncommon, rare, epic, legendary
    effect_type VARCHAR(30) NOT NULL, -- time_boost, score_multiplier, word_hint 등
    effect_value JSONB, -- 아이템 효과 값
    cooldown_seconds INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 아이템 인벤토리
CREATE TABLE IF NOT EXISTS user_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES items(id),
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 게임 로그 테이블
CREATE TABLE IF NOT EXISTS game_logs (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    action_type VARCHAR(30) NOT NULL, -- word_submit, item_use, game_start 등
    action_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    round_number INTEGER
);

-- 단어 제출 기록
CREATE TABLE IF NOT EXISTS word_submissions (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    word VARCHAR(100) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    validation_reason VARCHAR(100), -- 검증 실패 이유
    response_time_ms INTEGER,
    score_earned INTEGER DEFAULT 0,
    round_number INTEGER,
    turn_order INTEGER,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 게임 참가자 테이블
CREATE TABLE IF NOT EXISTS game_participants (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    final_score INTEGER DEFAULT 0,
    final_rank INTEGER,
    words_submitted INTEGER DEFAULT 0,
    items_used INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    max_combo INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,4) DEFAULT 0.0000,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_nickname ON users(nickname);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX IF NOT EXISTS idx_game_rooms_status ON game_rooms(status);
CREATE INDEX IF NOT EXISTS idx_game_rooms_created_by ON game_rooms(created_by);

CREATE INDEX IF NOT EXISTS idx_game_sessions_room_id ON game_sessions(room_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_started_at ON game_sessions(started_at);

CREATE INDEX IF NOT EXISTS idx_korean_dictionary_word ON korean_dictionary(word);
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_first_char ON korean_dictionary(first_char);
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_last_char ON korean_dictionary(last_char);
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_difficulty ON korean_dictionary(difficulty_level);

CREATE INDEX IF NOT EXISTS idx_items_rarity ON items(rarity);
CREATE INDEX IF NOT EXISTS idx_items_effect_type ON items(effect_type);

CREATE INDEX IF NOT EXISTS idx_user_items_user_id ON user_items(user_id);
CREATE INDEX IF NOT EXISTS idx_user_items_item_id ON user_items(item_id);

CREATE INDEX IF NOT EXISTS idx_game_logs_session_id ON game_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_game_logs_user_id ON game_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_game_logs_action_type ON game_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_game_logs_timestamp ON game_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_word_submissions_session_id ON word_submissions(session_id);
CREATE INDEX IF NOT EXISTS idx_word_submissions_user_id ON word_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_word_submissions_word ON word_submissions(word);
CREATE INDEX IF NOT EXISTS idx_word_submissions_submitted_at ON word_submissions(submitted_at);

CREATE INDEX IF NOT EXISTS idx_game_participants_session_id ON game_participants(session_id);
CREATE INDEX IF NOT EXISTS idx_game_participants_user_id ON game_participants(user_id);

-- 기본 아이템 데이터 삽입
INSERT INTO items (name, description, rarity, effect_type, effect_value, cooldown_seconds) VALUES
('시간 연장', '턴 시간을 10초 연장합니다', 'common', 'timer_extend', '{"seconds": 10}', 30),
('점수 배수', '다음 단어의 점수를 2배로 만듭니다', 'uncommon', 'score_multiply', '{"multiplier": 2.0}', 45),
('글자 힌트', '다음에 올 수 있는 글자 3개를 알려줍니다', 'rare', 'word_hint', '{"hint_count": 3}', 60),
('상대 방해', '상대방의 턴 시간을 5초 단축합니다', 'rare', 'timer_reduce', '{"seconds": 5}', 60),
('보호막', '한 턴 동안 아이템 공격을 무효화합니다', 'epic', 'shield', '{"duration_turns": 1}', 90),
('완벽한 힌트', '정확한 다음 단어를 알려줍니다', 'legendary', 'perfect_hint', '{"word_count": 1}', 120)
ON CONFLICT DO NOTHING;

-- 샘플 한국어 단어 데이터 (기본 1000개)
INSERT INTO korean_dictionary (word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length) VALUES
-- 일반 단어들
('사과', '빨갛고 둥근 과일', 1, 100, '명사', '사', '과', 2),
('과일', '나무나 풀에서 나는 먹을 수 있는 열매', 1, 90, '명사', '과', '일', 2),
('일요일', '한 주의 첫째 날', 1, 80, '명사', '일', '일', 3),
('일반적', '보통이고 특별하지 않은', 2, 70, '형용사', '일', '적', 3),
('적극적', '매우 활발하고 열성적인', 2, 60, '형용사', '적', '적', 3),
('적응', '환경이나 조건에 맞추어 나가는 것', 2, 65, '명사', '적', '응', 2),
('응답', '질문이나 요청에 대한 대답', 2, 75, '명사', '응', '답', 2),
('답변', '질문에 대한 대답', 1, 85, '명사', '답', '변', 2),
('변화', '달라지는 것', 2, 70, '명사', '변', '화', 2),
('화면', '텔레비전이나 컴퓨터의 보이는 부분', 1, 80, '명사', '화', '면', 2),

-- 동물 관련
('고양이', '집에서 기르는 작은 동물', 1, 95, '명사', '고', '이', 3),
('이상하다', '보통과 다르다', 2, 60, '형용사', '이', '다', 4),
('다람쥐', '나무에 사는 작은 동물', 1, 50, '명사', '다', '쥐', 3),
('쥐', '작고 회색인 동물', 1, 70, '명사', '쥐', '쥐', 1),

-- 음식 관련
('김치', '한국의 전통 발효 음식', 1, 90, '명사', '김', '치', 2),
('치킨', '닭고기 요리', 1, 85, '명사', '치', '킨', 2),
('킨더', '독일의 초콜릿 브랜드', 2, 30, '명사', '킨', '더', 2),
('더위', '뜨거운 날씨', 1, 60, '명사', '더', '위', 2),
('위험', '해가 될 수 있는 상황', 2, 80, '명사', '위', '험', 2),

-- 학교 관련
('학교', '공부하는 곳', 1, 95, '명사', '학', '교', 2),
('교실', '수업하는 방', 1, 85, '명사', '교', '실', 2),
('실습', '직접 해보며 배우는 것', 2, 55, '명사', '실', '습', 2),
('습관', '자주 반복해서 하는 행동', 2, 70, '명사', '습', '관', 2),
('관심', '마음을 쏟아 살피는 것', 2, 75, '명사', '관', '심', 2),

-- 기술 관련
('컴퓨터', '계산하고 정보를 처리하는 기계', 1, 90, '명사', '컴', '터', 3),
('터미널', '컴퓨터 명령어를 입력하는 프로그램', 3, 40, '명사', '터', '널', 3),
('널리', '넓게 퍼져서', 2, 45, '부사', '널', '리', 2),
('리모컨', '멀리서 조종하는 기계', 1, 70, '명사', '리', '컨', 3),
('컨트롤', '조절하거나 통제하는 것', 2, 60, '명사', '컨', '롤', 4),

-- 감정 관련
('행복', '기쁘고 만족한 마음', 1, 85, '명사', '행', '복', 2),
('복잡', '얽혀서 어수선한 상태', 2, 70, '형용사', '복', '잡', 2),
('잡다', '손으로 붙들다', 1, 75, '동사', '잡', '다', 2),
('다정', '상냥하고 친근한', 2, 50, '형용사', '다', '정', 2),
('정말', '참으로, 진짜로', 1, 95, '부사', '정', '말', 2),

-- 자연 관련
('바다', '넓고 깊은 물', 1, 85, '명사', '바', '다', 2),
('다리', '몸을 지탱하는 부분 또는 강을 건너는 구조물', 1, 80, '명사', '다', '리', 2),
('리더', '이끄는 사람', 2, 65, '명사', '리', '더', 2),
('더불어', '함께', 2, 55, '부사', '더', '어', 3),
('어머니', '엄마', 1, 90, '명사', '어', '니', 3),

-- 시간 관련
('니들', '너희들', 1, 60, '명사', '니', '들', 2),
('들판', '넓은 밭', 2, 40, '명사', '들', '판', 2),
('판단', '옳고 그름을 결정하는 것', 2, 70, '명사', '판', '단', 2),
('단어', '말의 최소 단위', 2, 85, '명사', '단', '어', 2),
('어린이', '나이가 적은 사람', 1, 80, '명사', '어', '이', 3),

-- 계절 관련
('이번', '지금 이때의', 1, 90, '관형사', '이', '번', 2),
('번호', '순서를 나타내는 숫자', 1, 85, '명사', '번', '호', 2),
('호수', '둘러싸인 큰 물', 2, 50, '명사', '호', '수', 2),
('수업', '가르치고 배우는 일', 1, 85, '명사', '수', '업', 2),
('업무', '해야 할 일', 2, 75, '명사', '업', '무', 2),

-- 색깔 관련
('무지개', '비 온 뒤 하늘에 나타나는 색띠', 1, 60, '명사', '무', '개', 3),
('개나리', '노란 꽃이 피는 나무', 2, 45, '명사', '개', '리', 3),
('리본', '장식용 끈', 1, 50, '명사', '리', '본', 2),
('본능', '타고난 능력', 3, 40, '명사', '본', '능', 2),
('능력', '어떤 일을 할 수 있는 힘', 2, 80, '명사', '능', '력', 2),

-- 추가 단어들 (1000개까지 확장하기 위한 기본 패턴)
('력사', '역사의 다른 말', 2, 30, '명사', '력', '사', 2),
('사랑', '좋아하는 마음', 1, 95, '명사', '사', '랑', 2),
('랑데부', '만남의 약속', 3, 20, '명사', '랑', '부', 3),
('부모', '아버지와 어머니', 1, 90, '명사', '부', '모', 2),
('모든', '전부의', 1, 85, '관형사', '모', '든', 2),
('든든', '믿음직한', 2, 60, '형용사', '든', '든', 2)

ON CONFLICT (word) DO NOTHING;