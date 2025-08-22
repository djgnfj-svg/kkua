#!/usr/bin/env python3
"""
간단한 끄투 데이터 변환 및 import (requests 없이)
"""

import psycopg2
import re
from typing import List, Tuple
import subprocess

class SimpleKKutuImporter:
    def __init__(self):
        self.db_config = {
            "host": "db",
            "port": "5432", 
            "database": "kkua_db",
            "user": "postgres",
            "password": "password"
        }
        
    def download_with_curl(self) -> List[str]:
        """curl로 끄투 단어 데이터 다운로드"""
        print("📡 curl로 끄투 단어 데이터 다운로드 중...")
        
        try:
            # curl로 kkutu_ko 테이블 데이터만 추출
            cmd = [
                "bash", "-c",
                "curl -s 'https://raw.githubusercontent.com/JJoriping/KKuTu/master/db.sql' | "
                "grep -A50000 'COPY kkutu_ko' | head -20000 | tail +2 | head -10000"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('\\')]
                print(f"📥 {len(lines)}줄의 데이터 다운로드 완료")
                return lines
            else:
                print(f"❌ 다운로드 실패: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"❌ 다운로드 오류: {e}")
            return []
    
    def parse_kkutu_words(self, data_lines: List[str]) -> List[Tuple]:
        """끄투 단어 데이터 파싱"""
        print("🔍 끄투 단어 데이터 파싱 중...")
        
        korean_words = []
        
        for line in data_lines:
            try:
                # 탭으로 분리
                parts = line.split('\t')
                if len(parts) < 4:
                    continue
                
                word = parts[0].strip()
                word_type = parts[1].strip()
                meaning = parts[2].strip().replace('＂1＂［1］（1）', '').strip()
                hit = int(parts[3].strip() or 0)
                
                # 한국어 단어만 필터링
                if not re.search(r'[가-힣]', word):
                    continue
                    
                if len(word) < 2 or len(word) > 10:
                    continue
                
                # 특수문자가 너무 많은 단어 제외
                if len(re.sub(r'[가-힣]', '', word)) > len(word) // 2:
                    continue
                
                # 빈도수를 점수로 변환
                frequency_score = min(max(hit * 3 + 30, 20), 100)
                
                # 난이도 계산
                if len(word) <= 3 and hit > 5:
                    difficulty = 1  # 쉬움
                elif len(word) <= 5:
                    difficulty = 2  # 보통
                else:
                    difficulty = 3  # 어려움
                
                # 첫글자, 끝글자
                first_char = word[0]
                last_char = word[-1]
                
                # 의미 정리
                if not meaning or meaning == '':
                    meaning = f"{word}의 뜻"
                
                korean_words.append((
                    word, meaning, difficulty, frequency_score,
                    "명사", first_char, last_char
                ))
                
            except Exception as e:
                continue
        
        # 중복 제거 (단어 기준)
        unique_words = {}
        for word_data in korean_words:
            word = word_data[0]
            if word not in unique_words:
                unique_words[word] = word_data
        
        final_words = list(unique_words.values())
        print(f"✅ {len(final_words)}개의 유효한 한국어 단어 파싱 완료")
        
        return final_words
    
    def import_to_database(self, words: List[Tuple]):
        """데이터베이스에 단어 import"""
        print("📥 데이터베이스에 끄투 단어 임포트 중...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 기존 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM korean_dictionary")
            before_count = cursor.fetchone()[0]
            print(f"🗃️ 기존 단어 개수: {before_count}개")
            
            insert_query = """
            INSERT INTO korean_dictionary 
            (word, definition, difficulty_level, frequency_score, word_type, first_char, last_char, word_length)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (word) DO UPDATE SET
                definition = EXCLUDED.definition,
                frequency_score = GREATEST(korean_dictionary.frequency_score, EXCLUDED.frequency_score);
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
                    
                    if success_count % 500 == 0:
                        print(f"📊 진행: {success_count}개 처리됨")
                        
                except Exception as e:
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
            
            print(f"✅ 끄투 단어 임포트 완료!")
            print(f"📊 성공: {success_count}개")
            print(f"📊 전체 단어 개수: {after_count}개 ({after_count - before_count}개 추가)")
            print(f"📈 난이도별 통계:")
            for level, count in difficulty_stats:
                level_name = {1: "쉬움", 2: "보통", 3: "어려움"}.get(level, f"레벨{level}")
                print(f"   {level_name}: {count}개")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ 데이터베이스 오류: {e}")

def main():
    print("🎮 끄투 실제 단어 데이터 import")
    print("=" * 50)
    
    importer = SimpleKKutuImporter()
    
    # 1. curl로 데이터 다운로드
    data_lines = importer.download_with_curl()
    if not data_lines:
        print("❌ 데이터 다운로드 실패")
        return
    
    # 2. 단어 데이터 파싱
    words = importer.parse_kkutu_words(data_lines)
    if not words:
        print("❌ 단어 파싱 실패")
        return
    
    # 3. 데이터베이스에 import
    importer.import_to_database(words)
    
    print("\n🎉 끄투 실제 데이터 import 완료!")

if __name__ == "__main__":
    main()