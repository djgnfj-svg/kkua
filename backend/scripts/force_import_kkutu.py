#!/usr/bin/env python3
"""
KKuTu 단어 데이터베이스 강제 임포트 스크립트 (중복 무시)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
import logging
from database import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_import_kkutu_words(file_path):
    """KKuTu 단어 리스트를 강제로 데이터베이스에 임포트 (중복 무시)"""
    
    # 데이터베이스 연결
    engine = create_engine(DATABASE_URL)
    
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            words = f.read().splitlines()
        
        logger.info(f"총 {len(words)}개의 단어를 찾았습니다.")
        
        # SQL 준비문 생성
        insert_sql = """
        INSERT INTO korean_dictionary (word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (word) DO NOTHING;
        """
        
        batch = []
        batch_size = 5000
        imported_count = 0
        skipped_count = 0
        
        for idx, word in enumerate(words):
            # 빈 줄이나 공백 제거
            word = word.strip()
            if not word:
                continue
            
            # 너무 짧거나 긴 단어 제외
            if len(word) < 2 or len(word) > 100:
                skipped_count += 1
                continue
            
            # 단어 정보 생성 (tuple로)
            word_data = (
                word,
                f'{word}의 뜻',
                min(max(1, len(word) - 1), 5),  # 길이 기반 난이도
                50,  # 기본 빈도
                '명사',  # 기본 품사
                word[0],  # 첫 글자
                word[-1],  # 마지막 글자
                len(word)  # 길이
            )
            
            batch.append(word_data)
            
            # 배치가 가득 차면 데이터베이스에 저장
            if len(batch) >= batch_size:
                try:
                    with engine.begin() as conn:
                        result = conn.execute(insert_sql, batch)
                        affected = result.rowcount if hasattr(result, 'rowcount') else len(batch)
                    imported_count += len(batch)
                    logger.info(f"진행률: {imported_count}/{len(words)} ({imported_count*100/len(words):.1f}%)")
                    batch = []
                except Exception as e:
                    logger.error(f"배치 저장 중 오류: {e}")
                    batch = []
        
        # 남은 배치 저장
        if batch:
            try:
                with engine.begin() as conn:
                    result = conn.execute(insert_sql, batch)
                imported_count += len(batch)
            except Exception as e:
                logger.error(f"마지막 배치 저장 중 오류: {e}")
        
        logger.info(f"임포트 완료: {imported_count}개 처리, {skipped_count}개 건너뜀")
        
        # 최종 단어 수 확인
        with engine.begin() as conn:
            result = conn.execute("SELECT COUNT(*) FROM korean_dictionary")
            total_count = result.fetchone()[0]
        logger.info(f"데이터베이스 총 단어 수: {total_count}개")
        
    except Exception as e:
        logger.error(f"임포트 중 오류 발생: {e}")

if __name__ == "__main__":
    file_path = "/tmp/kor_list.txt"
    if not os.path.exists(file_path):
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)
    
    logger.info("KKuTu 단어 데이터베이스 강제 임포트 시작...")
    force_import_kkutu_words(file_path)
    logger.info("임포트 완료!")