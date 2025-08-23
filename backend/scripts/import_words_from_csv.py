#!/usr/bin/env python3
"""
끄투 단어 CSV 파일을 데이터베이스에 import하는 간단한 스크립트
korean_words.csv 파일을 읽어서 PostgreSQL 데이터베이스에 저장
"""

import csv
import psycopg2
import os
from typing import List, Dict

class CSVWordImporter:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "db"),
            "port": os.getenv("DB_PORT", "5432"), 
            "database": os.getenv("DB_NAME", "kkua_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "password")
        }
        self.csv_file = "korean_words.csv"
        
    def load_words_from_csv(self) -> List[Dict]:
        """CSV 파일에서 단어 데이터 로드"""
        words = []
        csv_path = os.path.join(os.path.dirname(__file__), self.csv_file)
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    words.append({
                        'word': row['word'],
                        'definition': row['definition'],
                        'difficulty_level': int(row['difficulty_level']),
                        'frequency_score': int(row['frequency_score']),
                        'word_type': row['word_type'],
                        'first_char': row['first_char'],
                        'last_char': row['last_char'],
                        'word_length': int(row['word_length'])
                    })
            
            print(f"✅ CSV에서 {len(words)}개 단어 로드 완료")
            return words
            
        except FileNotFoundError:
            print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
            return []
        except Exception as e:
            print(f"❌ CSV 로드 오류: {e}")
            return []
    
    def import_to_database(self, words: List[Dict]):
        """단어를 데이터베이스에 import"""
        if not words:
            print("❌ import할 단어가 없습니다")
            return
            
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 기존 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM korean_dictionary")
            before_count = cursor.fetchone()[0]
            print(f"🗃️ 기존 단어 개수: {before_count}개")
            
            # 테이블 초기화 (선택사항 - 필요시 주석 해제)
            # cursor.execute("TRUNCATE TABLE korean_dictionary")
            # print("🗑️ 기존 데이터 삭제 완료")
            
            insert_query = """
            INSERT INTO korean_dictionary 
            (word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length)
            VALUES (%(word)s, %(definition)s, %(difficulty_level)s, %(frequency_score)s, 
                    %(word_type)s, %(first_char)s, %(last_char)s, %(word_length)s)
            ON CONFLICT (word) DO UPDATE SET
                definition = EXCLUDED.definition,
                difficulty_level = EXCLUDED.difficulty_level,
                frequency_score = GREATEST(korean_dictionary.frequency_score, EXCLUDED.frequency_score),
                word_type = EXCLUDED.word_type,
                first_char = EXCLUDED.first_char,
                last_char = EXCLUDED.last_char,
                word_length = EXCLUDED.word_length;
            """
            
            success_count = 0
            for word_data in words:
                try:
                    cursor.execute(insert_query, word_data)
                    success_count += 1
                    
                    if success_count % 1000 == 0:
                        print(f"📊 진행: {success_count}개 처리됨")
                        
                except Exception as e:
                    print(f"⚠️ 단어 '{word_data.get('word', 'unknown')}' 처리 실패: {e}")
                    continue
            
            conn.commit()
            
            # 결과 확인
            cursor.execute("SELECT COUNT(*) FROM korean_dictionary")
            after_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT difficulty_level, COUNT(*) 
                FROM korean_dictionary 
                GROUP BY difficulty_level 
                ORDER BY difficulty_level
            """)
            difficulty_stats = cursor.fetchall()
            
            cursor.execute("""
                SELECT first_char, COUNT(*) 
                FROM korean_dictionary 
                GROUP BY first_char 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            char_stats = cursor.fetchall()
            
            print(f"\n✅ CSV 단어 import 완료!")
            print(f"📊 성공: {success_count}개")
            print(f"📊 전체 단어 개수: {after_count}개 (변경: {after_count - before_count:+d}개)")
            
            print(f"\n📈 난이도별 통계:")
            for level, count in difficulty_stats:
                level_name = {1: "쉬움", 2: "보통", 3: "어려움"}.get(level, f"레벨{level}")
                print(f"   {level_name}: {count:,}개")
            
            print(f"\n📝 첫글자별 상위 10개:")
            for char, count in char_stats:
                print(f"   '{char}': {count:,}개")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ 데이터베이스 오류: {e}")

def main():
    print("🎮 끄투 단어 CSV Import")
    print("=" * 50)
    
    importer = CSVWordImporter()
    
    # CSV에서 단어 로드
    words = importer.load_words_from_csv()
    
    if words:
        # 데이터베이스에 import
        importer.import_to_database(words)
        print(f"\n🎉 {len(words):,}개 단어 import 완료!")
    else:
        print("❌ import 실패")

if __name__ == "__main__":
    main()