#!/usr/bin/env python3
"""
끄투 오픈소스 단어 데이터 가져오기 스크립트
GitHub: https://github.com/JJoriping/KKuTu
"""

import psycopg2
import json
import re
from typing import List, Tuple
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from kkutu_extended_words import get_extended_words

class KKutuWordImporter:
    def __init__(self):
        # 데이터베이스 연결 설정
        self.db_config = {
            "host": "db",  # Docker 네트워크 내 호스트명
            "port": "5432", 
            "database": "kkua_db",
            "user": "postgres",
            "password": "password"
        }
        
        # 끄투 단어 목록 (임시 - 실제로는 큰 데이터)
        self.sample_kkutu_words = [
            # 기본 한국어 단어들 (끄투 스타일)
            ("가방", "물건을 넣어 들고 다니는 것", 1, 90, "명사", "가", "방"),
            ("방문", "집에 찾아가는 것", 1, 85, "명사", "방", "문"),
            ("문제", "해결해야 할 것", 2, 80, "명사", "문", "제"),
            ("제출", "내어주는 것", 2, 70, "명사", "제", "출"),
            ("출입", "들어가고 나오는 것", 2, 75, "명사", "출", "입"),
            ("입구", "들어가는 곳", 1, 85, "명사", "입", "구"),
            ("구름", "하늘에 떠있는 흰 덩어리", 1, 80, "명사", "구", "름"),
            ("름차", "인도의 차", 3, 30, "명사", "름", "차"),
            ("차량", "탈 것", 2, 85, "명사", "차", "량"),
            ("량심", "마음의 소리", 3, 40, "명사", "량", "심"),
            
            # 좀 더 어려운 단어들
            ("가나다라", "한글 자음 순서", 2, 60, "명사", "가", "라"),
            ("라디오", "소리를 전파로 듣는 기계", 1, 70, "명사", "라", "오"),
            ("오리너구리", "물에 사는 동물", 3, 20, "명사", "오", "리"),
            ("리모컨", "멀리서 조종하는 것", 1, 90, "명사", "리", "컨"),
            ("컨테이너", "화물을 담는 큰 상자", 2, 50, "명사", "컨", "너"),
            ("너구리", "꼬리가 줄무늬인 동물", 1, 60, "명사", "너", "리"),
            
            # 공격/방어 단어들 (끄투 게임 특성)
            ("강낭콩", "콩의 한 종류", 1, 70, "명사", "강", "콩"),
            ("콩나물", "콩에서 나온 새싹", 1, 85, "명사", "콩", "물"),
            ("물고기", "물에서 사는 동물", 1, 90, "명사", "물", "기"),
            ("기차역", "기차가 서는 곳", 1, 80, "명사", "기", "역"),
            ("역사책", "역사에 관한 책", 2, 60, "명사", "역", "책"),
            ("책가방", "책을 넣는 가방", 1, 80, "명사", "책", "방"),
            
            # 긴 단어들 (끄투 고급 전략)
            ("가나다라마바사", "한글 자음", 3, 10, "명사", "가", "사"),
            ("사과나무열매", "사과나무에서 나는 열매", 2, 30, "명사", "사", "매"),
            ("매미나방나비", "곤충의 종류", 3, 5, "명사", "매", "비"),
            ("비행기조종사", "비행기를 모는 사람", 2, 40, "명사", "비", "사"),
            ("사자성어모음", "사자성어를 모은 것", 3, 15, "명사", "사", "음"),
            
            # 끝글자 'ㅇ' 단어들 (방어용)
            ("강아지", "개의 새끼", 1, 95, "명사", "강", "지"),
            ("지구온난화", "지구가 더워지는 현상", 3, 50, "명사", "지", "화"),
            ("화학반응", "물질이 변하는 현상", 3, 45, "명사", "화", "응"),
            ("응급처치", "급할 때 하는 치료", 2, 70, "명사", "응", "치"),
            ("치과의사", "치아를 치료하는 의사", 2, 75, "명사", "치", "사"),
            
            # 특수한 단어들
            ("국수나무늘보", "느린 동물", 3, 5, "명사", "국", "보"),
            ("보물상자열쇠", "보물상자를 여는 열쇠", 3, 10, "명사", "보", "쇠"),
            ("쇠고기볶음밥", "쇠고기로 만든 볶음밥", 2, 60, "명사", "쇠", "밥"),
            ("밥상다리소리", "밥상 다리에서 나는 소리", 3, 5, "명사", "밥", "리"),
            ("리어카바퀴", "리어카의 바퀴", 2, 20, "명사", "리", "퀴"),
        ]
    
    def get_kkutu_sample_data(self) -> List[Tuple]:
        """끄투 스타일 샘플 단어 데이터 반환"""
        # 기본 샘플 단어 + 확장 단어 결합
        all_words = self.sample_kkutu_words + get_extended_words()
        # 중복 제거 (단어를 기준으로)
        unique_words = {}
        for word_data in all_words:
            word = word_data[0]
            if word not in unique_words:
                unique_words[word] = word_data
        
        final_words = list(unique_words.values())
        print(f"📝 총 {len(final_words)}개의 끄투 스타일 단어를 준비했습니다.")
        return final_words
    
    def import_words_to_db(self, words: List[Tuple]):
        """단어 데이터를 데이터베이스에 임포트"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 기존 데이터 백업을 위한 확인
            cursor.execute("SELECT COUNT(*) FROM korean_dictionary")
            existing_count = cursor.fetchone()[0]
            print(f"🗃️ 기존 단어 개수: {existing_count}개")
            
            # 끄투 단어 삽입
            insert_query = """
            INSERT INTO korean_dictionary 
            (word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (word) DO UPDATE SET
                definition = EXCLUDED.definition,
                difficulty_level = EXCLUDED.difficulty_level,
                frequency_score = EXCLUDED.frequency_score,
                word_type = EXCLUDED.word_type;
            """
            
            success_count = 0
            for word_data in words:
                try:
                    word, definition, difficulty, frequency, word_type, first_char, last_char = word_data
                    word_length = len(word)
                    
                    cursor.execute(insert_query, (
                        word, definition, difficulty, frequency, word_type,
                        first_char, last_char, word_length
                    ))
                    success_count += 1
                    
                except Exception as e:
                    print(f"⚠️ 단어 '{word_data[0]}' 삽입 실패: {e}")
                    continue
            
            conn.commit()
            
            # 결과 확인
            cursor.execute("SELECT COUNT(*) FROM korean_dictionary")
            final_count = cursor.fetchone()[0]
            
            print(f"✅ 끄투 단어 임포트 완료!")
            print(f"📊 성공: {success_count}개")
            print(f"📊 전체 단어 개수: {final_count}개")
            
            # 난이도별 통계
            cursor.execute("""
                SELECT difficulty_level, COUNT(*) 
                FROM korean_dictionary 
                GROUP BY difficulty_level 
                ORDER BY difficulty_level
            """)
            
            difficulty_stats = cursor.fetchall()
            print(f"📈 난이도별 통계:")
            for level, count in difficulty_stats:
                level_name = {1: "쉬움", 2: "보통", 3: "어려움"}.get(level, f"레벨{level}")
                print(f"   {level_name}: {count}개")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ 데이터베이스 오류: {e}")
    
    def download_real_kkutu_data(self):
        """실제 끄투 데이터 다운로드 (참고용)"""
        print("📡 실제 끄투 데이터를 다운로드하려면:")
        print("1. https://github.com/JJoriping/KKuTu 에서 db.sql 다운로드")
        print("2. PostgreSQL에서 kkutu 테이블 추출")
        print("3. 아래 명령어로 변환:")
        print("""
        # PostgreSQL에서 끄투 단어 추출
        psql -h localhost -U postgres -d kkutu_original -c "
        \\COPY (
            SELECT word, '', 2, 50, '명사', 
                   LEFT(word, 1), RIGHT(word, 1), LENGTH(word)
            FROM kkutu_ko 
            WHERE LENGTH(word) >= 2 AND LENGTH(word) <= 10
            LIMIT 10000
        ) TO 'kkutu_words.csv' WITH CSV;
        "
        """)
    
    def validate_imported_words(self):
        """임포트된 단어 검증"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 끝말잇기 체인 테스트
            test_cases = [
                ("사과", "과"),
                ("과일", "일"),
                ("일요일", "일"),
                ("강아지", "지")
            ]
            
            print("🔍 끝말잇기 체인 테스트:")
            for word, last_char in test_cases:
                cursor.execute("""
                    SELECT word FROM korean_dictionary 
                    WHERE first_char = %s 
                    ORDER BY frequency_score DESC 
                    LIMIT 5
                """, (last_char,))
                
                next_words = [row[0] for row in cursor.fetchall()]
                print(f"   {word} → {last_char}로 시작: {', '.join(next_words[:3])}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ 검증 오류: {e}")

def main():
    print("🎮 끄투 스타일 단어 데이터 임포트 시작")
    print("=" * 50)
    
    importer = KKutuWordImporter()
    
    # 1. 샘플 데이터 가져오기
    words = importer.get_kkutu_sample_data()
    
    # 2. 데이터베이스에 임포트
    print("\n📥 데이터베이스에 임포트 중...")
    importer.import_words_to_db(words)
    
    # 3. 검증
    print("\n🔍 임포트 결과 검증 중...")
    importer.validate_imported_words()
    
    # 4. 실제 끄투 데이터 다운로드 안내
    print("\n💡 더 많은 단어가 필요하면:")
    importer.download_real_kkutu_data()
    
    print("\n🎉 끄투 단어 임포트 완료!")

if __name__ == "__main__":
    main()