#!/usr/bin/env python3
"""
방해 아이템들을 데이터베이스에 추가하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from database import engine
from models.item_models import Item

# 새로운 방해 아이템들
DISTRACTION_ITEMS = [
    {
        "name": "고양이 방해 😸",
        "description": "상대방 화면에 귀여운 고양이들이 지나다니며 집중력을 방해합니다",
        "rarity": "rare",
        "effect_type": "cat_distraction",
        "effect_value": {
            "duration": 5,
            "cat_count": 3,
            "target_type": "all_opponents"
        },
        "cooldown_seconds": 45
    },
    {
        "name": "화면 흔들기 📳",
        "description": "상대방의 화면을 흔들어 입력을 방해합니다",
        "rarity": "uncommon",
        "effect_type": "screen_shake",
        "effect_value": {
            "duration": 3,
            "intensity": "medium",
            "target_type": "current_player"
        },
        "cooldown_seconds": 30
    },
    {
        "name": "화면 흐림 😵‍💫",
        "description": "상대방의 화면을 흐리게 만들어 단어 입력을 어렵게 합니다",
        "rarity": "rare",
        "effect_type": "blur_screen",
        "effect_value": {
            "duration": 4,
            "blur_level": 3,
            "target_type": "current_player"
        },
        "cooldown_seconds": 40
    },
    {
        "name": "잎사귀 비 🍃",
        "description": "화면 위로 잎사귀들이 떨어져 내려 시야를 가립니다",
        "rarity": "common",
        "effect_type": "falling_objects",
        "effect_value": {
            "duration": 6,
            "object_type": "leaves",
            "target_type": "all_opponents"
        },
        "cooldown_seconds": 25
    },
    {
        "name": "하트 비 💕",
        "description": "화면 위로 하트들이 떨어져 내려 집중력을 방해합니다",
        "rarity": "uncommon",
        "effect_type": "falling_objects",
        "effect_value": {
            "duration": 5,
            "object_type": "hearts",
            "target_type": "all_opponents"
        },
        "cooldown_seconds": 35
    },
    {
        "name": "별빛 비 ⭐",
        "description": "화면 위로 별들이 떨어져 내려 환상적인 방해를 만듭니다",
        "rarity": "rare",
        "effect_type": "falling_objects",
        "effect_value": {
            "duration": 7,
            "object_type": "stars",
            "target_type": "all_opponents"
        },
        "cooldown_seconds": 50
    },
    {
        "name": "색상 반전 🎨",
        "description": "상대방의 화면 색상을 반전시켜 혼란을 야기합니다",
        "rarity": "epic",
        "effect_type": "color_invert",
        "effect_value": {
            "duration": 5,
            "target_type": "current_player"
        },
        "cooldown_seconds": 60
    },
    {
        "name": "눈송이 비 ❄️",
        "description": "화면 위로 눈송이들이 내려 겨울 분위기와 함께 방해합니다",
        "rarity": "uncommon",
        "effect_type": "falling_objects",
        "effect_value": {
            "duration": 8,
            "object_type": "snow",
            "target_type": "all_opponents"
        },
        "cooldown_seconds": 40
    }
]


def add_distraction_items():
    """방해 아이템들을 데이터베이스에 추가"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        added_count = 0
        updated_count = 0
        
        for item_data in DISTRACTION_ITEMS:
            # 기존 아이템 확인
            existing_item = session.query(Item).filter_by(
                name=item_data["name"]
            ).first()
            
            if existing_item:
                # 기존 아이템 업데이트
                existing_item.description = item_data["description"]
                existing_item.rarity = item_data["rarity"]
                existing_item.effect_type = item_data["effect_type"]
                existing_item.effect_value = item_data["effect_value"]
                existing_item.cooldown_seconds = item_data["cooldown_seconds"]
                updated_count += 1
                print(f"✅ 아이템 업데이트: {item_data['name']}")
            else:
                # 새 아이템 추가
                new_item = Item(
                    name=item_data["name"],
                    description=item_data["description"],
                    rarity=item_data["rarity"],
                    effect_type=item_data["effect_type"],
                    effect_value=item_data["effect_value"],
                    cooldown_seconds=item_data["cooldown_seconds"],
                    is_active=True
                )
                session.add(new_item)
                added_count += 1
                print(f"✅ 아이템 추가: {item_data['name']}")
        
        # 변경사항 저장
        session.commit()
        
        print(f"\n🎉 방해 아이템 추가 완료!")
        print(f"   새로 추가: {added_count}개")
        print(f"   업데이트: {updated_count}개")
        print(f"   총 아이템: {added_count + updated_count}개")
        
        # 전체 아이템 수 확인
        total_items = session.query(Item).filter_by(is_active=True).count()
        print(f"   데이터베이스 내 활성 아이템 총 개수: {total_items}개")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("🎮 방해 아이템 추가 스크립트 실행")
    print("=" * 50)
    add_distraction_items()
    print("=" * 50)
    print("✨ 완료! 이제 게임에서 새로운 아이템을 사용할 수 있습니다.")