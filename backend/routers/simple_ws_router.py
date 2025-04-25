from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Set
import json
from datetime import datetime
import random

router = APIRouter(
    prefix="/simple-ws",
    tags=["websocket-test"],
)

# 간단한 연결 관리자
class SimpleConnectionManager:
    def __init__(self):
        # 활성 연결 저장 (client_id: WebSocket)
        self.active_connections: Dict[str, WebSocket] = {}
        # 사용자 닉네임 저장
        self.user_names: Dict[str, str] = {}
        # 다음 클라이언트 ID
        self.next_client_id = 1
        
        # 게임 관련 상태
        self.game_in_progress = False
        self.game_players: List[str] = []  # 게임 참여자 client_id 목록
        self.current_player_index = 0  # 현재 차례 인덱스
        self.current_word: Optional[str] = None  # 현재 단어
        self.used_words: Set[str] = set()  # 사용된 단어들
        self.game_turn_timeout = None  # 턴 타임아웃 추적용
    
    def generate_client_id(self) -> str:
        """새 클라이언트 ID 생성"""
        client_id = f"client_{self.next_client_id}"
        self.next_client_id += 1
        return client_id
    
    async def connect(self, websocket: WebSocket) -> str:
        """새 클라이언트 연결 처리"""
        await websocket.accept()
        client_id = self.generate_client_id()
        self.active_connections[client_id] = websocket
        self.user_names[client_id] = f"사용자_{client_id}"
        
        print(f"새 연결 추가: {client_id}")
        return client_id
    
    def disconnect(self, client_id: str):
        """클라이언트 연결 해제"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if client_id in self.user_names:
            del self.user_names[client_id]
            
        print(f"연결 종료: {client_id}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """특정 클라이언트에게 메시지 전송"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))
    
    async def broadcast(self, message: dict, exclude: str = None):
        """모든 클라이언트에게 메시지 브로드캐스트"""
        # 기본 메시지 필드 추가
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
            
        for client_id, connection in list(self.active_connections.items()):
            if exclude and client_id == exclude:
                continue  # 제외할 클라이언트 건너뛰기
                
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"메시지 전송 오류 ({client_id}): {str(e)}")
                # 오류 발생 시 연결 제거
                self.disconnect(client_id)
    
    def set_username(self, client_id: str, username: str) -> bool:
        """사용자 이름 설정"""
        if client_id in self.active_connections:
            self.user_names[client_id] = username
            return True
        return False
    
    def get_username(self, client_id: str) -> str:
        """사용자 이름 조회"""
        return self.user_names.get(client_id, f"손님_{client_id}")
    
    def get_active_users(self) -> List[dict]:
        """현재 활성 사용자 목록 반환"""
        return [
            {"client_id": client_id, "username": self.get_username(client_id)}
            for client_id in self.active_connections.keys()
        ]
    
    async def start_game(self):
        """끝말잇기 게임 시작"""
        if self.game_in_progress:
            return False, "게임이 이미 진행 중입니다."
            
        # 최소 2명 이상의 플레이어가 필요
        if len(self.active_connections) < 2:
            return False, "게임을 시작하려면 최소 2명 이상의 플레이어가 필요합니다."
            
        # 게임 상태 초기화
        self.game_in_progress = True
        self.game_players = list(self.active_connections.keys())
        random.shuffle(self.game_players)  # 플레이어 순서 랜덤화
        self.current_player_index = 0
        self.current_word = None
        self.used_words.clear()
        
        return True, "게임이 시작되었습니다."
    
    def end_game(self, reason: str = "게임 종료"):
        """끝말잇기 게임 종료"""
        self.game_in_progress = False
        self.game_players = []
        self.current_word = None
        return reason
    
    def get_current_player(self) -> Optional[str]:
        """현재 차례인 플레이어의 client_id 반환"""
        if not self.game_in_progress or not self.game_players:
            return None
        return self.game_players[self.current_player_index]
    
    def next_player_turn(self) -> str:
        """다음 플레이어로 턴 넘기기"""
        if not self.game_in_progress or not self.game_players:
            return None
            
        self.current_player_index = (self.current_player_index + 1) % len(self.game_players)
        return self.game_players[self.current_player_index]
    
    def validate_word(self, word: str) -> tuple[bool, str]:
        """단어 유효성 검증"""
        # 이미 사용된 단어인지 확인
        if word in self.used_words:
            return False, "이미 사용된 단어입니다."
            
        # 첫 단어는 항상 유효
        if self.current_word is None:
            self.current_word = word
            self.used_words.add(word)
            return True, "첫 단어가 등록되었습니다."
            
        # 끝말잇기 규칙 검증: 이전 단어의 마지막 글자로 시작하는지
        if self.current_word[-1] != word[0]:
            return False, f"'{self.current_word}'의 마지막 글자 '{self.current_word[-1]}'로 시작하는 단어여야 합니다."
            
        # 유효한 단어
        self.current_word = word
        self.used_words.add(word)
        return True, "단어가 승인되었습니다."
    
    def get_game_status(self) -> dict:
        """현재 게임 상태 정보 반환"""
        if not self.game_in_progress:
            return {
                "game_in_progress": False
            }
            
        current_player_id = self.get_current_player()
        return {
            "game_in_progress": True,
            "current_player": {
                "client_id": current_player_id,
                "username": self.get_username(current_player_id)
            },
            "current_word": self.current_word,
            "used_words": list(self.used_words),
            "players": [
                {"client_id": player_id, "username": self.get_username(player_id)}
                for player_id in self.game_players
            ]
        }

# 연결 관리자 인스턴스 생성
connection_manager = SimpleConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """간단한 웹소켓 엔드포인트"""
    client_id = await connection_manager.connect(websocket)
    
    # 연결 성공 메시지
    await connection_manager.send_personal_message({
        "type": "connected",
        "client_id": client_id,
        "message": f"연결 성공! 당신의 ID는 {client_id}입니다.",
        "timestamp": datetime.utcnow().isoformat()
    }, client_id)
    
    # 새 사용자 입장 알림
    await connection_manager.broadcast({
        "type": "user_joined",
        "client_id": client_id,
        "username": connection_manager.get_username(client_id),
        "message": f"{connection_manager.get_username(client_id)}님이 입장했습니다.",
        "users": connection_manager.get_active_users()
    }, exclude=None)  # 모든 사용자에게 브로드캐스트
    
    try:
        # 메시지 수신 루프
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)
            print(f"메시지 수신 from {client_id}: {message_data}")
            
            # 메시지 유형에 따른 처리
            message_type = message_data.get("type", "")
            
            if message_type == "chat":
                # 채팅 메시지 브로드캐스트
                chat_message = {
                    "type": "chat",
                    "client_id": client_id,
                    "username": connection_manager.get_username(client_id),
                    "message": message_data.get("message", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
                await connection_manager.broadcast(chat_message)
                
            elif message_type == "set_username":
                # 사용자 이름 설정
                new_username = message_data.get("username", "")
                if new_username:
                    old_username = connection_manager.get_username(client_id)
                    connection_manager.set_username(client_id, new_username)
                    
                    # 이름 변경 알림
                    await connection_manager.broadcast({
                        "type": "username_changed",
                        "client_id": client_id,
                        "old_username": old_username,
                        "new_username": new_username,
                        "message": f"{old_username}님이 이름을 {new_username}으로 변경했습니다.",
                        "users": connection_manager.get_active_users()
                    })
            
            elif message_type == "ping":
                # 핑-퐁 메시지
                await connection_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
                
            elif message_type == "start_game":
                # 게임 시작 처리
                success, message = await connection_manager.start_game()
                
                if success:
                    # 게임 시작 알림
                    current_player = connection_manager.get_current_player()
                    await connection_manager.broadcast({
                        "type": "game_started",
                        "message": "끝말잇기 게임이 시작되었습니다!",
                        "game_status": connection_manager.get_game_status()
                    })
                else:
                    # 게임 시작 실패 알림
                    await connection_manager.send_personal_message({
                        "type": "game_error",
                        "message": message
                    }, client_id)
            
            elif message_type == "submit_word":
                # 단어 제출 처리
                if not connection_manager.game_in_progress:
                    await connection_manager.send_personal_message({
                        "type": "game_error",
                        "message": "게임이 진행 중이 아닙니다."
                    }, client_id)
                    continue
                    
                # 플레이어 턴 확인
                current_player = connection_manager.get_current_player()
                if client_id != current_player:
                    await connection_manager.send_personal_message({
                        "type": "game_error",
                        "message": "당신의 차례가 아닙니다."
                    }, client_id)
                    continue
                
                word = message_data.get("word", "").strip()
                if not word:
                    await connection_manager.send_personal_message({
                        "type": "game_error",
                        "message": "단어를 입력해주세요."
                    }, client_id)
                    continue
                
                # 단어 유효성 검증
                is_valid, reason = connection_manager.validate_word(word)
                
                if is_valid:
                    # 다음 플레이어로 턴 넘기기
                    next_player = connection_manager.next_player_turn()
                    
                    await connection_manager.broadcast({
                        "type": "word_accepted",
                        "client_id": client_id,
                        "username": connection_manager.get_username(client_id),
                        "word": word,
                        "message": reason,
                        "next_player": {
                            "client_id": next_player,
                            "username": connection_manager.get_username(next_player)
                        },
                        "game_status": connection_manager.get_game_status()
                    })
                else:
                    # 단어 거부 알림
                    await connection_manager.broadcast({
                        "type": "word_rejected",
                        "client_id": client_id,
                        "username": connection_manager.get_username(client_id),
                        "word": word,
                        "reason": reason,
                        "game_status": connection_manager.get_game_status()
                    })
            
            elif message_type == "end_game":
                # 게임 종료 처리
                if connection_manager.game_in_progress:
                    reason = connection_manager.end_game("게임이 종료되었습니다.")
                    
                    await connection_manager.broadcast({
                        "type": "game_over",
                        "message": reason,
                        "requester": {
                            "client_id": client_id,
                            "username": connection_manager.get_username(client_id)
                        }
                    })
                
    except WebSocketDisconnect:
        # 연결 종료 처리
        username = connection_manager.get_username(client_id)
        
        # 게임 중인 경우 처리
        if connection_manager.game_in_progress and client_id in connection_manager.game_players:
            reason = connection_manager.end_game(f"{username}님이 연결을 종료하여 게임이 취소되었습니다.")
            
            # 남은 사용자들에게 게임 종료 알림
            await connection_manager.broadcast({
                "type": "game_over",
                "message": reason
            })
        
        connection_manager.disconnect(client_id)
        
        # 사용자 퇴장 알림
        await connection_manager.broadcast({
            "type": "user_left",
            "client_id": client_id,
            "username": username,
            "message": f"{username}님이 퇴장했습니다.",
            "users": connection_manager.get_active_users()
        })
    
    except Exception as e:
        # 기타 예외 처리
        print(f"웹소켓 오류 ({client_id}): {str(e)}")
        connection_manager.disconnect(client_id)

@router.get("/")
def get_test_page():
    """테스트 페이지 안내"""
    return {
        "message": "웹소켓 테스트 페이지는 /static/websocket_test.html에서 접근할 수 있습니다.",
        "websocket_url": "/simple-ws/ws"
    } 