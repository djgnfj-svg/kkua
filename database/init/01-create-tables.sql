-- 끄투 DB 테이블 생성 및 인덱스
CREATE TABLE IF NOT EXISTS korean_dictionary (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) UNIQUE NOT NULL,
    definition VARCHAR(500) DEFAULT '',
    difficulty_level INTEGER DEFAULT 1,
    frequency_score INTEGER DEFAULT 50,
    word_type VARCHAR(20) DEFAULT '명사',
    first_char CHAR(1) NOT NULL,
    last_char CHAR(1) NOT NULL,
    word_length INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 성능 최적화 인덱스
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_word ON korean_dictionary(word);
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_first_char ON korean_dictionary(first_char);
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_last_char ON korean_dictionary(last_char);
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_word_length ON korean_dictionary(word_length);

-- 끝말잇기 성능을 위한 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_korean_dictionary_first_last ON korean_dictionary(first_char, last_char);

-- 통계 정보
ANALYZE korean_dictionary;