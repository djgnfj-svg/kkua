#!/usr/bin/env python3
"""
다중 사용자 끝말잇기 게임 테스트 스크립트
실제 여러 WebSocket 연결을 통해 게임을 시뮬레이션합니다.
"""

import asyncio
import websockets
import json
import time
import requests
from typing import List, Dict, Any

class GameUser:
    def __init__(self, nickname: str):
        self.nickname = nickname
        self.user_id = None
        self.session_token = None
        self.websocket = None
        self.room_id = None
        self.is_connected = False
        
    async def login(self):
        """게스트 로그인"""
        try:
            response = requests.post('http://localhost:8000/auth/login', 
                                   json={'nickname': self.nickname})
            if response.status_code == 200:
                data = response.json()
                self.user_id = data['user_id']
                self.session_token = data['session_token']
                print(f"✅ {self.nickname} 로그인 성공 (ID: {self.user_id})")
                return True
        except Exception as e:
            print(f"❌ {self.nickname} 로그인 실패: {e}")
        return False
    
    async def connect_websocket(self, room_id: str):
        """WebSocket 연결"""
        try:
            uri = f"ws://localhost:8000/ws/rooms/{room_id}?token={self.session_token}"
            self.websocket = await websockets.connect(uri)
            self.room_id = room_id
            self.is_connected = True
            print(f"🔗 {self.nickname} WebSocket 연결 성공")
            
            # 방 입장 메시지 전송
            await self.send_message('join_room', {'room_id': room_id})
            return True
        except Exception as e:
            print(f"❌ {self.nickname} WebSocket 연결 실패: {e}")
        return False
    
    async def send_message(self, msg_type: str, data: Dict[str, Any] = None):
        """메시지 전송"""
        if not self.websocket:
            return False
        
        message = {
            'type': msg_type,
            'data': data or {},
            'timestamp': time.time()
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 {self.nickname}: {msg_type}")
            return True
        except Exception as e:
            print(f"❌ {self.nickname} 메시지 전송 실패: {e}")
        return False
    
    async def listen_messages(self):
        """메시지 수신 대기"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except Exception as e:
            print(f"❌ {self.nickname} 메시지 수신 오류: {e}")
    
    async def handle_message(self, data: Dict[str, Any]):
        """메시지 처리"""
        msg_type = data.get('type', '')
        msg_data = data.get('data', {})
        
        if msg_type == 'connection_established':
            print(f"✅ {self.nickname} 연결 확립됨")
        
        elif msg_type == 'room_joined':
            print(f"🏠 {self.nickname} 방 입장 성공")
        
        elif msg_type == 'game_started':
            current_player = msg_data.get('current_turn_nickname', '알 수 없음')
            print(f"🎮 {self.nickname}: 게임 시작! 현재 차례: {current_player}")
        
        elif msg_type == 'turn_timer_started':
            if msg_data.get('user_id') == int(self.user_id):
                print(f"⏰ {self.nickname}: 내 차례 시작! ({msg_data.get('time_limit')}초)")
                # 자동으로 단어 입력 (간단한 단어들)
                words = ['사과', '과자', '자동차', '차표', '표범', '범인', '인간', '간식', '식당', '당근']
                word = words[int(time.time()) % len(words)]
                await asyncio.sleep(2)  # 2초 대기 후 입력
                await self.send_message('submit_word', {'word': word})
        
        elif msg_type == 'word_submitted':
            if msg_data.get('status') == 'accepted':
                submitter = msg_data.get('nickname', '알 수 없음')
                word = msg_data.get('word', '')
                next_char = msg_data.get('next_char', '')
                next_player = msg_data.get('current_turn_nickname', '')
                print(f"📝 {self.nickname}: {submitter}님이 '{word}' 제출 → 다음: {next_player}님 ('{next_char}'로 시작)")
        
        elif msg_type == 'word_submission_failed':
            reason = msg_data.get('reason', '알 수 없는 오류')
            print(f"❌ {self.nickname}: 단어 제출 실패 - {reason}")
        
        elif msg_type == 'turn_timeout':
            timeout_user = msg_data.get('timeout_nickname', '알 수 없음')
            current_player = msg_data.get('current_turn_nickname', '알 수 없음')
            print(f"⏱️ {self.nickname}: {timeout_user}님 타임아웃 → {current_player}님 차례")
        
        elif msg_type == 'error':
            error_msg = msg_data.get('message', '알 수 없는 오류')
            print(f"🚫 {self.nickname}: 오류 - {error_msg}")
    
    async def start_game(self):
        """게임 시작"""
        await asyncio.sleep(1)
        await self.send_message('start_game')
        print(f"🎯 {self.nickname}: 게임 시작 요청")
    
    async def disconnect(self):
        """연결 종료"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            print(f"🔌 {self.nickname} 연결 종료")

async def test_multi_user_game():
    """다중 사용자 게임 테스트"""
    print("🎮 끄아(KKUA) 다중 사용자 테스트 시작!")
    print("=" * 60)
    
    # 테스트 방 생성
    try:
        response = requests.post('http://localhost:8000/gamerooms',
                               json={'name': '자동 테스트 방 🤖', 'max_players': 4})
        if response.status_code == 200:
            room_data = response.json()
            room_id = room_data['room_id']
            print(f"🏠 테스트 방 생성 성공: {room_id}")
        else:
            print("❌ 테스트 방 생성 실패")
            return
    except Exception as e:
        print(f"❌ 테스트 방 생성 오류: {e}")
        return
    
    # 테스트 사용자들 생성
    users = [
        GameUser("봇1호"),
        GameUser("봇2호"),
        GameUser("봇3호")
    ]
    
    # 1단계: 모든 사용자 로그인
    print("\n📝 1단계: 사용자 로그인")
    for user in users:
        if not await user.login():
            print(f"❌ {user.nickname} 로그인 실패로 테스트 중단")
            return
    
    # 2단계: WebSocket 연결
    print("\n🔗 2단계: WebSocket 연결")
    for user in users:
        if not await user.connect_websocket(room_id):
            print(f"❌ {user.nickname} WebSocket 연결 실패")
            return
    
    # 3단계: 메시지 리스닝 시작
    print("\n👂 3단계: 메시지 수신 시작")
    listen_tasks = []
    for user in users:
        task = asyncio.create_task(user.listen_messages())
        listen_tasks.append(task)
    
    # 짧은 대기 후 게임 시작
    await asyncio.sleep(3)
    
    # 4단계: 게임 시작 (첫 번째 사용자가 시작)
    print("\n🎮 4단계: 게임 시작")
    await users[0].start_game()
    
    # 5단계: 게임 진행 관찰 (60초)
    print("\n⏰ 5단계: 게임 진행 관찰 (60초)")
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 테스트 중단")
    
    # 6단계: 정리
    print("\n🧹 6단계: 연결 정리")
    for task in listen_tasks:
        task.cancel()
    
    for user in users:
        await user.disconnect()
    
    print("\n✅ 다중 사용자 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_multi_user_game())