#!/usr/bin/env python3
"""
간소화된 게임 WebSocket 테스트 스크립트
실제 게임 플로우 테스트
"""

import asyncio
import websockets
import json
import sys

async def test_game_flow():
    """완전한 게임 플로우 테스트"""
    
    print("🎮 간소화된 게임 시스템 테스트 시작")
    
    # 두 명의 플레이어가 같은 게임에 접속
    game_url1 = "ws://localhost:8000/ws/game/rooms/1"
    game_url2 = "ws://localhost:8000/ws/game/rooms/1"
    
    try:
        # 첫 번째 플레이어 접속
        print("👤 플레이어 1 접속 중...")
        websocket1 = await websockets.connect(game_url1)
        
        # 두 번째 플레이어 접속
        print("👤 플레이어 2 접속 중...")  
        websocket2 = await websockets.connect(game_url2)
        
        # 초기 메시지들 받기
        print("\n📨 초기 메시지 수신 중...")
        
        # 플레이어 1의 게임 참가 메시지
        msg1 = await websocket1.recv()
        data1 = json.loads(msg1)
        print(f"플레이어 1: {data1['type']} - {data1.get('message', '')}")
        
        if data1['type'] == 'game_joined':
            print(f"   시작 단어: {data1['game_state'].get('start_word', 'N/A')}")
            print(f"   내 턴: {data1['your_turn']}")
            print(f"   현재 플레이어: {data1.get('current_player', {}).get('nickname', 'N/A')}")
        
        # 플레이어 2의 게임 참가 메시지
        msg2 = await websocket2.recv()
        data2 = json.loads(msg2)
        print(f"플레이어 2: {data2['type']} - {data2.get('message', '')}")
        
        # 플레이어 조인 브로드캐스트 메시지들
        try:
            while True:
                msg = await asyncio.wait_for(websocket1.recv(), timeout=2.0)
                data = json.loads(msg)
                print(f"📢 브로드캐스트: {data['type']} - {data.get('message', '')}")
                
                if data['type'] == 'game_started_with_word':
                    print(f"   🎯 게임 시작!")
                    print(f"   시작 단어: {data['start_word']}")
                    print(f"   다음 글자: '{data['last_char']}'")
                    print(f"   첫 번째 플레이어: {data['current_player']['nickname']}")
                    break
        except asyncio.TimeoutError:
            print("⚠️  게임 시작 메시지를 받지 못했습니다.")
            
        # 간단한 단어 게임 테스트
        print("\n🎯 단어 게임 테스트")
        
        # 첫 번째 플레이어가 단어 제출 (시작 단어에 따라 달라짐)
        test_words = ["과일", "일기장", "장난감", "감사", "사랑"]
        
        for i, word in enumerate(test_words[:3]):  # 3개 단어만 테스트
            print(f"\n턴 {i+1}: '{word}' 제출")
            
            # 현재 턴인 플레이어 확인 후 단어 제출
            submit_data = {
                "type": "submit_word",
                "word": word,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            if i % 2 == 0:  # 플레이어 1
                await websocket1.send(json.dumps(submit_data))
                print(f"   플레이어 1이 '{word}' 제출")
            else:  # 플레이어 2  
                await websocket2.send(json.dumps(submit_data))
                print(f"   플레이어 2가 '{word}' 제출")
            
            # 결과 메시지 받기
            try:
                for ws in [websocket1, websocket2]:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    data = json.loads(msg)
                    
                    if data['type'] == 'word_accepted':
                        print(f"   ✅ 단어 승인: {data['word']}")
                        print(f"   다음 글자: '{data['last_char']}'")
                        print(f"   다음 플레이어: {data['next_player']}")
                        break
                    elif data['type'] == 'error':
                        print(f"   ❌ 오류: {data['message']}")
                        break
                        
            except asyncio.TimeoutError:
                print("   ⚠️  응답 메시지 타임아웃")
                
            await asyncio.sleep(1)  # 잠시 대기
        
        print("\n🎉 게임 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        
    finally:
        # 연결 정리
        try:
            await websocket1.close()
            await websocket2.close()
        except:
            pass
        
        print("🔌 연결 종료")

if __name__ == "__main__":
    print("간소화된 게임 WebSocket 테스트")
    print("=" * 50)
    
    try:
        asyncio.run(test_game_flow())
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 오류: {e}")
        sys.exit(1)