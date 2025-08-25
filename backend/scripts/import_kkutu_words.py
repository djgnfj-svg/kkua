#!/usr/bin/env python3
"""
KKuTu 단어 데이터베이스 임포트 스크립트
AutoKkutu의 kor_list.txt 파일에서 단어를 가져와 PostgreSQL에 저장
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import DATABASE_URL
from models.dictionary_models import KoreanDictionary
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_kkutu_words(file_path):
    """KKuTu 단어 리스트를 데이터베이스에 임포트"""
    
    # 데이터베이스 연결
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            words = f.read().splitlines()
        
        logger.info(f"총 {len(words)}개의 단어를 찾았습니다.")
        
        # 배치 처리를 위한 리스트
        batch = []
        batch_size = 1000
        imported_count = 0
        skipped_count = 0
        
        for idx, word in enumerate(words):
            # 빈 줄이나 공백 제거
            word = word.strip()
            if not word:
                continue
            
            # 너무 짧거나 긴 단어 제외 (1글자 또는 100글자 초과)
            if len(word) < 2 or len(word) > 100:
                skipped_count += 1
                continue
            
            # 중복 체크 비활성화 - 모든 단어 강제 추가
            # existing = session.query(KoreanDictionary).filter_by(word=word).first()
            # if existing:
            #     skipped_count += 1
            #     continue
            
            # 단어 정보 생성
            word_data = {
                'word': word,
                'definition': f'{word}의 뜻',  # 기본 정의
                'difficulty_level': min(max(1, len(word) - 1), 5),  # 길이 기반 난이도 (1-5)
                'frequency_score': 50,  # 기본 빈도
                'word_type': '명사',  # 기본 품사
                'first_char': word[0],
                'last_char': word[-1],
                'word_length': len(word)
            }
            
            batch.append(word_data)
            
            # 배치가 가득 차면 데이터베이스에 저장
            if len(batch) >= batch_size:
                try:
                    # ON CONFLICT DO NOTHING을 사용하여 중복 건너뛰기
                    insert_stmt = """
                    INSERT INTO korean_dictionary (word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length)
                    VALUES (%(word)s, %(definition)s, %(difficulty_level)s, %(frequency_score)s, %(word_type)s, %(first_char)s, %(last_char)s, %(word_length)s)
                    ON CONFLICT (word) DO NOTHING
                    """
                    session.execute(text(insert_stmt), batch)
                    session.commit()
                    imported_count += len(batch)
                    logger.info(f"진행률: {imported_count}/{len(words)} ({imported_count*100/len(words):.1f}%)")
                    batch = []
                except Exception as e:
                    logger.error(f"배치 저장 중 오류: {e}")
                    session.rollback()
                    batch = []
        
        # 남은 배치 저장
        if batch:
            try:
                insert_stmt = """
                INSERT INTO korean_dictionary (word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length)
                VALUES (%(word)s, %(definition)s, %(difficulty_level)s, %(frequency_score)s, %(word_type)s, %(first_char)s, %(last_char)s, %(word_length)s)
                ON CONFLICT (word) DO NOTHING
                """
                session.execute(text(insert_stmt), batch)
                session.commit()
                imported_count += len(batch)
            except Exception as e:
                logger.error(f"마지막 배치 저장 중 오류: {e}")
                session.rollback()
        
        logger.info(f"임포트 완료: {imported_count}개 추가, {skipped_count}개 건너뜀")
        
        # 최종 단어 수 확인
        total_count = session.query(KoreanDictionary).count()
        logger.info(f"데이터베이스 총 단어 수: {total_count}개")
        
    except Exception as e:
        logger.error(f"임포트 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    file_path = "/tmp/kor_list.txt"
    if not os.path.exists(file_path):
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)
    
    logger.info("KKuTu 단어 데이터베이스 임포트 시작...")
    import_kkutu_words(file_path)
    logger.info("임포트 완료!")