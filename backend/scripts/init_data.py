"""
기본 데이터 삽입 스크립트
아이템, 한국어 단어 등의 초기 데이터를 데이터베이스에 삽입
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Item, KoreanDictionary
import logging

logger = logging.getLogger(__name__)


def insert_items(db: Session):
    """기본 아이템 데이터 삽입"""
    items_data = [
        {
            "name": "시간 연장",
            "description": "턴 시간을 10초 연장합니다",
            "rarity": "common",
            "effect_type": "timer_extend",
            "effect_value": {"seconds": 10},
            "cooldown_seconds": 30
        },
        {
            "name": "점수 배수",
            "description": "다음 단어의 점수를 2배로 만듭니다",
            "rarity": "uncommon",
            "effect_type": "score_multiply",
            "effect_value": {"multiplier": 2.0},
            "cooldown_seconds": 45
        },
        {
            "name": "글자 힌트",
            "description": "다음에 올 수 있는 글자 3개를 알려줍니다",
            "rarity": "rare",
            "effect_type": "word_hint",
            "effect_value": {"hint_count": 3},
            "cooldown_seconds": 60
        },
        {
            "name": "상대 방해",
            "description": "상대방의 턴 시간을 5초 단축합니다",
            "rarity": "rare",
            "effect_type": "timer_reduce",
            "effect_value": {"seconds": 5, "target": "opponent"},
            "cooldown_seconds": 60
        },
        {
            "name": "보호막",
            "description": "한 턴 동안 아이템 공격을 무효화합니다",
            "rarity": "epic",
            "effect_type": "shield",
            "effect_value": {"duration_turns": 1},
            "cooldown_seconds": 90
        },
        {
            "name": "완벽한 힌트",
            "description": "정확한 다음 단어를 알려줍니다",
            "rarity": "legendary",
            "effect_type": "perfect_hint",
            "effect_value": {"word_count": 1},
            "cooldown_seconds": 120
        },
        {
            "name": "연쇄 점수",
            "description": "다음 3턴 동안 점수를 1.5배로 만듭니다",
            "rarity": "epic",
            "effect_type": "score_chain",
            "effect_value": {"multiplier": 1.5, "duration_turns": 3},
            "cooldown_seconds": 120
        },
        {
            "name": "시간 정지",
            "description": "상대방들의 타이머를 3초간 정지시킵니다",
            "rarity": "legendary",
            "effect_type": "time_freeze",
            "effect_value": {"freeze_seconds": 3, "target": "all_opponents"},
            "cooldown_seconds": 180
        }
    ]
    
    for item_data in items_data:
        # 중복 확인
        existing_item = db.query(Item).filter(Item.name == item_data["name"]).first()
        if not existing_item:
            item = Item(**item_data)
            db.add(item)
            logger.info(f"아이템 추가: {item_data['name']}")
    
    db.commit()
    logger.info("아이템 데이터 삽입 완료")


def insert_korean_words(db: Session):
    """한국어 단어 데이터 삽입 (CSV 파일에서만 로드)"""
    import csv
    import os
    
    logger = logging.getLogger(__name__)
    
    # CSV 파일에서만 단어 로드
    words_data = []
    
    # CSV 파일에서 확장 단어 데이터 읽기
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'data', 'korean_words.csv')
    
    if os.path.exists(csv_file_path):
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row_num, row in enumerate(reader, 1):
                    if len(row) >= 5:  # 최소 5개 컬럼 필요
                        # CSV 형식: 단어,설명,난이도,빈도,품사,첫글자,마지막글자,길이
                        word_entry = {
                            "word": row[0].strip(),
                            "definition": row[1].strip(),
                            "difficulty_level": int(row[2]) if row[2].isdigit() else 1,
                            "frequency_score": int(row[3]) if row[3].isdigit() else 50,
                            "word_type": row[4].strip() if len(row) > 4 else '명사'
                        }
                        
                        # 필수 필드가 있고 유효한 단어인 경우만 추가
                        if word_entry["word"] and len(word_entry["word"]) > 0:
                            words_data.append(word_entry)
            
            csv_words_count = len(words_data)  # CSV에서만 로드
            logger.info(f"CSV에서 {csv_words_count} 개의 단어를 로드했습니다")
        except Exception as e:
            logger.warning(f"CSV 파일 읽기 실패: {e}")
    else:
        logger.warning("CSV 파일이 없습니다")
    
    # 중복 제거를 위한 단어 집합
    unique_words = {}
    for word_data in words_data:
        word = word_data["word"]
        # 첫 번째 등장한 단어만 유지
        if word not in unique_words:
            unique_words[word] = word_data
    
    logger.info(f"총 {len(unique_words)}개의 고유 단어를 처리합니다.")
    
    # 기존 단어들을 한번에 조회하여 중복 확인 최적화
    existing_words_query = db.query(KoreanDictionary.word).all()
    existing_words_set = {row.word for row in existing_words_query}
    logger.info(f"기존 DB에 {len(existing_words_set)}개의 단어가 있습니다.")
    
    # 데이터베이스에 삽입할 단어들만 필터링
    words_to_insert = []
    processed_count = 0
    
    for word_data in unique_words.values():
        processed_count += 1
        if processed_count % 10000 == 0:
            logger.info(f"처리 진행률: {processed_count}/{len(unique_words)} ({processed_count/len(unique_words)*100:.1f}%)")
        
        # 중복 확인 (메모리 내에서 빠르게 처리)
        if word_data["word"] not in existing_words_set:
            # 첫 글자와 마지막 글자 계산
            word = word_data["word"]
            first_char = word[0] if word else ''
            last_char = word[-1] if word else ''
            
            korean_word = KoreanDictionary(
                word=word_data["word"],
                definition=word_data["definition"],
                difficulty_level=word_data["difficulty_level"],
                frequency_score=word_data["frequency_score"],
                word_type=word_data["word_type"],
                first_char=first_char,
                last_char=last_char,
                word_length=len(word)
            )
            
            words_to_insert.append(korean_word)
    
    logger.info(f"삽입할 새로운 단어: {len(words_to_insert)}개")
    
    # 초고속 배치 삽입 (bulk_insert_mappings 사용)
    if words_to_insert:
        # 객체를 딕셔너리로 변환 (bulk_insert_mappings용)
        words_dict_list = []
        for word_obj in words_to_insert:
            words_dict_list.append({
                'word': word_obj.word,
                'definition': word_obj.definition,
                'difficulty_level': word_obj.difficulty_level,
                'frequency_score': word_obj.frequency_score,
                'word_type': word_obj.word_type,
                'first_char': word_obj.first_char,
                'last_char': word_obj.last_char,
                'word_length': word_obj.word_length
            })
        
        batch_size = 10000  # 더 큰 배치 크기
        total_batches = (len(words_dict_list) + batch_size - 1) // batch_size
        
        logger.info(f"초고속 bulk insert 시작: {total_batches}개 배치로 처리")
        
        for i in range(0, len(words_dict_list), batch_size):
            batch = words_dict_list[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"배치 {batch_num}/{total_batches} 삽입 중... ({len(batch)}개 단어)")
            
            # SQLAlchemy의 bulk_insert_mappings 사용 (매우 빠름)
            db.bulk_insert_mappings(KoreanDictionary, batch)
            db.commit()
            
            logger.info(f"배치 {batch_num} 완료")
        
        logger.info(f"총 {len(words_to_insert)}개의 새로운 단어 삽입 완료")
    
    logger.info("한국어 단어 데이터 삽입 완료")


def main():
    """메인 실행 함수"""
    # 모든 테이블 생성
    from models import Base
    Base.metadata.create_all(bind=engine)
    
    # 데이터베이스 세션 생성
    db = SessionLocal()
    
    try:
        logger.info("초기 데이터 삽입 시작")
        
        # 아이템 삽입
        insert_items(db)
        
        # 한국어 단어 삽입
        insert_korean_words(db)
        
        logger.info("모든 초기 데이터 삽입 완료")
        
    except Exception as e:
        logger.error(f"데이터 삽입 중 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()