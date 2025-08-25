-- 끄투 단어 데이터 임포트 (CSV COPY 방식 - 가장 빠름)
\echo '끄투 단어 데이터 임포트 시작...'

-- CSV 데이터 고속 임포트
COPY korean_dictionary(word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length)
FROM '/docker-entrypoint-initdb.d/data/korean_words.csv'
DELIMITER ','
CSV HEADER;

-- 임포트 결과 확인
\echo '임포트 완료! 총 단어 수:'
SELECT COUNT(*) as total_words FROM korean_dictionary;

-- 첫글자별 통계
\echo '첫글자별 단어 수 (상위 10개):'
SELECT first_char, COUNT(*) as count 
FROM korean_dictionary 
GROUP BY first_char 
ORDER BY count DESC 
LIMIT 10;

-- 길이별 통계
\echo '단어 길이별 분포:'
SELECT word_length, COUNT(*) as count
FROM korean_dictionary
GROUP BY word_length
ORDER BY word_length;

-- 샘플 단어 확인
\echo '샘플 단어 (10개):'
SELECT word, first_char, last_char, word_length
FROM korean_dictionary
WHERE word_length BETWEEN 2 AND 5
ORDER BY RANDOM()
LIMIT 10;

-- 성능 최적화
VACUUM ANALYZE korean_dictionary;

\echo '끄투 DB 구축 완료! 🎮'