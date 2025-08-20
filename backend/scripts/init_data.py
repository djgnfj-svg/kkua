"""
기본 데이터 삽입 스크립트
아이템, 한국어 단어 등의 초기 데이터를 데이터베이스에 삽입
"""

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
    """한국어 단어 데이터 삽입"""
    from .extended_words import EXTENDED_KOREAN_WORDS
    
    # 기본 단어 데이터
    words_data = [
        # 일반 단어들 (난이도 1)
        {"word": "사과", "definition": "빨갛고 둥근 과일", "difficulty_level": 1, "frequency_score": 100, "word_type": "명사"},
        {"word": "과일", "definition": "나무나 풀에서 나는 먹을 수 있는 열매", "difficulty_level": 1, "frequency_score": 90, "word_type": "명사"},
        {"word": "일요일", "definition": "한 주의 첫째 날", "difficulty_level": 1, "frequency_score": 80, "word_type": "명사"},
        {"word": "일반적", "definition": "보통이고 특별하지 않은", "difficulty_level": 2, "frequency_score": 70, "word_type": "형용사"},
        {"word": "적극적", "definition": "매우 활발하고 열성적인", "difficulty_level": 2, "frequency_score": 60, "word_type": "형용사"},
        {"word": "적응", "definition": "환경이나 조건에 맞추어 나가는 것", "difficulty_level": 2, "frequency_score": 65, "word_type": "명사"},
        {"word": "응답", "definition": "질문이나 요청에 대한 대답", "difficulty_level": 2, "frequency_score": 75, "word_type": "명사"},
        {"word": "답변", "definition": "질문에 대한 대답", "difficulty_level": 1, "frequency_score": 85, "word_type": "명사"},
        {"word": "변화", "definition": "달라지는 것", "difficulty_level": 2, "frequency_score": 70, "word_type": "명사"},
        {"word": "화면", "definition": "텔레비전이나 컴퓨터의 보이는 부분", "difficulty_level": 1, "frequency_score": 80, "word_type": "명사"},
        
        # 동물 관련
        {"word": "고양이", "definition": "집에서 기르는 작은 동물", "difficulty_level": 1, "frequency_score": 95, "word_type": "명사"},
        {"word": "이상하다", "definition": "보통과 다르다", "difficulty_level": 2, "frequency_score": 60, "word_type": "형용사"},
        {"word": "다람쥐", "definition": "나무에 사는 작은 동물", "difficulty_level": 1, "frequency_score": 50, "word_type": "명사"},
        {"word": "쥐", "definition": "작고 회색인 동물", "difficulty_level": 1, "frequency_score": 70, "word_type": "명사"},
        {"word": "강아지", "definition": "개의 새끼", "difficulty_level": 1, "frequency_score": 95, "word_type": "명사"},
        {"word": "지렁이", "definition": "땅속에 사는 긴 벌레", "difficulty_level": 1, "frequency_score": 40, "word_type": "명사"},
        
        # 음식 관련
        {"word": "김치", "definition": "한국의 전통 발효 음식", "difficulty_level": 1, "frequency_score": 90, "word_type": "명사"},
        {"word": "치킨", "definition": "닭고기 요리", "difficulty_level": 1, "frequency_score": 85, "word_type": "명사"},
        {"word": "킨더", "definition": "독일의 초콜릿 브랜드", "difficulty_level": 2, "frequency_score": 30, "word_type": "명사"},
        {"word": "더위", "definition": "뜨거운 날씨", "difficulty_level": 1, "frequency_score": 60, "word_type": "명사"},
        {"word": "위험", "definition": "해가 될 수 있는 상황", "difficulty_level": 2, "frequency_score": 80, "word_type": "명사"},
        {"word": "험난", "definition": "어렵고 위험함", "difficulty_level": 3, "frequency_score": 30, "word_type": "형용사"},
        
        # 학교 관련
        {"word": "학교", "definition": "공부하는 곳", "difficulty_level": 1, "frequency_score": 95, "word_type": "명사"},
        {"word": "교실", "definition": "수업하는 방", "difficulty_level": 1, "frequency_score": 85, "word_type": "명사"},
        {"word": "실습", "definition": "직접 해보며 배우는 것", "difficulty_level": 2, "frequency_score": 55, "word_type": "명사"},
        {"word": "습관", "definition": "자주 반복해서 하는 행동", "difficulty_level": 2, "frequency_score": 70, "word_type": "명사"},
        {"word": "관심", "definition": "마음을 쏟아 살피는 것", "difficulty_level": 2, "frequency_score": 75, "word_type": "명사"},
        
        # 기술 관련
        {"word": "컴퓨터", "definition": "계산하고 정보를 처리하는 기계", "difficulty_level": 1, "frequency_score": 90, "word_type": "명사"},
        {"word": "터미널", "definition": "컴퓨터 명령어를 입력하는 프로그램", "difficulty_level": 3, "frequency_score": 40, "word_type": "명사"},
        {"word": "널리", "definition": "넓게 퍼져서", "difficulty_level": 2, "frequency_score": 45, "word_type": "부사"},
        {"word": "리모컨", "definition": "멀리서 조종하는 기계", "difficulty_level": 1, "frequency_score": 70, "word_type": "명사"},
        {"word": "컨트롤", "definition": "조절하거나 통제하는 것", "difficulty_level": 2, "frequency_score": 60, "word_type": "명사"},
        
        # 감정 관련
        {"word": "행복", "definition": "기쁘고 만족한 마음", "difficulty_level": 1, "frequency_score": 85, "word_type": "명사"},
        {"word": "복잡", "definition": "얽혀서 어수선한 상태", "difficulty_level": 2, "frequency_score": 70, "word_type": "형용사"},
        {"word": "잡다", "definition": "손으로 붙들다", "difficulty_level": 1, "frequency_score": 75, "word_type": "동사"},
        {"word": "다정", "definition": "상냥하고 친근한", "difficulty_level": 2, "frequency_score": 50, "word_type": "형용사"},
        {"word": "정말", "definition": "참으로, 진짜로", "difficulty_level": 1, "frequency_score": 95, "word_type": "부사"},
        
        # 자연 관련
        {"word": "바다", "definition": "넓고 깊은 물", "difficulty_level": 1, "frequency_score": 85, "word_type": "명사"},
        {"word": "다리", "definition": "몸을 지탱하는 부분 또는 강을 건너는 구조물", "difficulty_level": 1, "frequency_score": 80, "word_type": "명사"},
        {"word": "리더", "definition": "이끄는 사람", "difficulty_level": 2, "frequency_score": 65, "word_type": "명사"},
        {"word": "더불어", "definition": "함께", "difficulty_level": 2, "frequency_score": 55, "word_type": "부사"},
        {"word": "어머니", "definition": "엄마", "difficulty_level": 1, "frequency_score": 90, "word_type": "명사"},
        
        # 시간 관련
        {"word": "니들", "definition": "너희들", "difficulty_level": 1, "frequency_score": 60, "word_type": "대명사"},
        {"word": "들판", "definition": "넓은 밭", "difficulty_level": 2, "frequency_score": 40, "word_type": "명사"},
        {"word": "판단", "definition": "옳고 그름을 결정하는 것", "difficulty_level": 2, "frequency_score": 70, "word_type": "명사"},
        {"word": "단어", "definition": "말의 최소 단위", "difficulty_level": 2, "frequency_score": 85, "word_type": "명사"},
        {"word": "어린이", "definition": "나이가 적은 사람", "difficulty_level": 1, "frequency_score": 80, "word_type": "명사"},
        
        # 계절 관련
        {"word": "이번", "definition": "지금 이때의", "difficulty_level": 1, "frequency_score": 90, "word_type": "관형사"},
        {"word": "번호", "definition": "순서를 나타내는 숫자", "difficulty_level": 1, "frequency_score": 85, "word_type": "명사"},
        {"word": "호수", "definition": "둘러싸인 큰 물", "difficulty_level": 2, "frequency_score": 50, "word_type": "명사"},
        {"word": "수업", "definition": "가르치고 배우는 일", "difficulty_level": 1, "frequency_score": 85, "word_type": "명사"},
        {"word": "업무", "definition": "해야 할 일", "difficulty_level": 2, "frequency_score": 75, "word_type": "명사"},
        
        # 색깔 관련
        {"word": "무지개", "definition": "비 온 뒤 하늘에 나타나는 색띠", "difficulty_level": 1, "frequency_score": 60, "word_type": "명사"},
        {"word": "개나리", "definition": "노란 꽃이 피는 나무", "difficulty_level": 2, "frequency_score": 45, "word_type": "명사"},
        {"word": "리본", "definition": "장식용 끈", "difficulty_level": 1, "frequency_score": 50, "word_type": "명사"},
        {"word": "본능", "definition": "타고난 능력", "difficulty_level": 3, "frequency_score": 40, "word_type": "명사"},
        {"word": "능력", "definition": "어떤 일을 할 수 있는 힘", "difficulty_level": 2, "frequency_score": 80, "word_type": "명사"},
        
        # 추가 단어들
        {"word": "력사", "definition": "역사의 다른 말", "difficulty_level": 2, "frequency_score": 30, "word_type": "명사"},
        {"word": "사랑", "definition": "좋아하는 마음", "difficulty_level": 1, "frequency_score": 95, "word_type": "명사"},
        {"word": "랑데부", "definition": "만남의 약속", "difficulty_level": 3, "frequency_score": 20, "word_type": "명사"},
        {"word": "부모", "definition": "아버지와 어머니", "difficulty_level": 1, "frequency_score": 90, "word_type": "명사"},
        {"word": "모든", "definition": "전부의", "difficulty_level": 1, "frequency_score": 85, "word_type": "관형사"},
        {"word": "든든", "definition": "믿음직한", "difficulty_level": 2, "frequency_score": 60, "word_type": "형용사"},
        
        # 게임 관련 추가 단어들
        {"word": "게임", "definition": "재미를 위한 놀이", "difficulty_level": 1, "frequency_score": 90, "word_type": "명사"},
        {"word": "임무", "definition": "맡은 일이나 책임", "difficulty_level": 2, "frequency_score": 65, "word_type": "명사"},
        {"word": "무기", "definition": "싸울 때 쓰는 도구", "difficulty_level": 1, "frequency_score": 70, "word_type": "명사"},
        {"word": "기회", "definition": "좋은 때나 경우", "difficulty_level": 2, "frequency_score": 80, "word_type": "명사"},
        {"word": "회전", "definition": "둥글게 돌리는 것", "difficulty_level": 2, "frequency_score": 60, "word_type": "명사"},
        {"word": "전투", "definition": "싸우는 것", "difficulty_level": 2, "frequency_score": 55, "word_type": "명사"},
        {"word": "투표", "definition": "의견을 나타내기 위해 표를 던지는 것", "difficulty_level": 2, "frequency_score": 70, "word_type": "명사"},
        {"word": "표현", "definition": "생각이나 느낌을 나타내는 것", "difficulty_level": 2, "frequency_score": 75, "word_type": "명사"},
        {"word": "현실", "definition": "실제로 존재하는 것", "difficulty_level": 2, "frequency_score": 80, "word_type": "명사"},
        {"word": "실제", "definition": "정말로 있는", "difficulty_level": 2, "frequency_score": 75, "word_type": "형용사"}
    ]
    
    # 확장 단어 데이터 추가
    words_data.extend(EXTENDED_KOREAN_WORDS)
    
    # 중복 제거를 위한 단어 집합
    unique_words = {}
    
    # 첫 글자, 마지막 글자, 단어 길이 자동 계산 및 중복 제거
    for word_data in words_data:
        word = word_data["word"]
        if word not in unique_words:
            word_data["first_char"] = word[0]
            word_data["last_char"] = word[-1]
            word_data["word_length"] = len(word)
            unique_words[word] = word_data
    
    logger.info(f"총 {len(unique_words)}개의 고유 단어를 처리합니다.")
    
    # 배치로 삽입 (성능 향상)
    words_to_insert = []
    for word, word_data in unique_words.items():
        # 데이터베이스 중복 확인
        existing_word = db.query(KoreanDictionary).filter(KoreanDictionary.word == word).first()
        if not existing_word:
            words_to_insert.append(KoreanDictionary(**word_data))
            
    if words_to_insert:
        db.add_all(words_to_insert)
        logger.info(f"{len(words_to_insert)}개 단어를 데이터베이스에 추가합니다.")
    
    db.commit()
    logger.info("한국어 단어 데이터 삽입 완료")


def insert_initial_data():
    """모든 초기 데이터 삽입"""
    db = SessionLocal()
    try:
        logger.info("기본 데이터 삽입 시작")
        
        # 아이템 데이터 삽입
        insert_items(db)
        
        # 한국어 단어 데이터 삽입
        insert_korean_words(db)
        
        logger.info("모든 기본 데이터 삽입 완료")
        
    except Exception as e:
        logger.error(f"기본 데이터 삽입 중 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 직접 실행시 데이터 삽입
    insert_initial_data()