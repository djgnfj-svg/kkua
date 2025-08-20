from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
import asyncio
from datetime import datetime
import uuid
import random

router = APIRouter(prefix="/ws/game", tags=["simple-game-websockets"])
logger = logging.getLogger(__name__)

# 게임 상태 저장소
game_sessions = {}  # {room_id: {players, current_player, words_used, game_state, etc}}
game_connections = {}  # {room_id: {user_id: websocket}}

# 한국어 끝말잇기 단어 검증을 위한 간단한 단어 리스트 (예시)
KOREAN_WORDS = {
    '사과', '과일', '일어나다', '다리', '리본', '본격적', '적극적', '적당히',
    '사자', '자동차', '차가운', '운동', '동물', '물고기', '기차', '차례',
    '바나나', '나비', '비행기', '기분', '분위기', '기회', '회사', '사람',
    '컴퓨터', '터널', '널빤지', '지구', '구름', '름직한', '한국', '국가',
    '학교', '교실', '실수', '수박', '박물관', '관심', '심장', '장미',
    '미소', '소나무', '무료', '료리', '리더', '더위', '위험', '험악한',
    '안녕', '녕길', '길이', '이야기', '기억', '억지', '지혜', '혜택',
    '택시', '시간', '간식', '식당', '당연히', '히터', '터미널', '널리'
}

# 게임 시작용 단어들 (끝말잇기하기 좋은 단어들)
START_WORDS = ['사과', '바나나', '학교', '컴퓨터', '사자', '자동차', '미소', '택시']

def is_valid_word_chain(prev_word: str, new_word: str) -> bool:
    """간단한 끝말잇기 검증"""
    if not prev_word or not new_word:
        return False
    
    if new_word not in KOREAN_WORDS:
        return False
    
    # 마지막 글자와 첫 글자가 일치하는지 확인
    return prev_word[-1] == new_word[0]

def get_last_char(word: str) -> str:
    """단어의 마지막 글자 반환"""
    return word[-1] if word else ""

async def broadcast_to_game(room_id: int, message: dict):
    """게임 참가자들에게 메시지 브로드캐스트"""
    if room_id not in game_connections:
        return
        
    for user_id, websocket in game_connections[room_id].items():
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # 연결이 끊어진 경우 무시
            pass

def init_game_session(room_id: int, players: list):
    """게임 세션 초기화"""
    # 랜덤 시작 단어 선택
    start_word = random.choice(START_WORDS)
    # 랜덤하게 첫 번째 플레이어 선택
    random.shuffle(players)
    
    game_sessions[room_id] = {
        "players": players,
        "current_player_index": 0,
        "words_used": [],
        "game_state": "starting",  # 시작 상태로 변경
        "turn_timeout": 30,
        "start_time": datetime.now().isoformat(),
        "last_word": start_word,  # 시작 단어 설정
        "start_word": start_word,  # 시작 단어 별도 저장
        "scores": {player["guest_id"]: 0 for player in players},
        "current_player": players[0]  # 현재 플레이어 정보 추가
    }

@router.websocket("/rooms/{room_id}")
async def simple_game_websocket(websocket: WebSocket, room_id: int):
    """간소화된 게임 WebSocket"""
    
    await websocket.accept()
    
    # 임시 사용자 정보 생성 (실제로는 인증에서 가져와야 함)
    user_id = str(uuid.uuid4())[:8]
    user_nickname = f"플레이어{user_id[:4]}"
    
    logger.info(f"🎮 게임 접속: room_id={room_id}, user={user_nickname}")
    
    try:
        # 연결 저장
        if room_id not in game_connections:
            game_connections[room_id] = {}
        
        game_connections[room_id][user_id] = websocket
        
        # 게임 세션이 없으면 생성 (첫 번째 플레이어)
        if room_id not in game_sessions:
            players = [{"guest_id": user_id, "nickname": user_nickname}]
            init_game_session(room_id, players)
        else:
            # 기존 게임에 플레이어 추가
            existing_player = next((p for p in game_sessions[room_id]["players"] if p["guest_id"] == user_id), None)
            if not existing_player:
                game_sessions[room_id]["players"].append({"guest_id": user_id, "nickname": user_nickname})
        
        # 게임 상태 전송
        game_state = game_sessions[room_id]
        current_player = game_state["players"][game_state["current_player_index"]]
        
        await websocket.send_text(json.dumps({
            "type": "game_joined",
            "message": f"{user_nickname}님이 게임에 참가했습니다!",
            "game_state": game_state,
            "your_turn": current_player["guest_id"] == user_id,
            "current_player": current_player,
            "timestamp": datetime.now().isoformat()
        }))
        
        # 다른 플레이어들에게 알림
        updated_game_state = game_sessions[room_id]
        current_player = updated_game_state["players"][updated_game_state["current_player_index"]]
        
        await broadcast_to_game(room_id, {
            "type": "player_joined",
            "message": f"🎮 {user_nickname}님이 게임에 참가했습니다!",
            "players": updated_game_state["players"],
            "game_state": updated_game_state,
            "current_player": current_player,
            "timestamp": datetime.now().isoformat()
        })
        
        # 게임이 시작 상태면 게임 시작 안내 메시지 전송
        if updated_game_state["game_state"] == "starting":
            await asyncio.sleep(1)  # 잠시 대기
            await start_game_announcement(room_id)
        
        # 메시지 처리 루프
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                logger.info(f"📨 게임 메시지: {user_nickname} -> {msg}")
                
                if msg.get("type") == "submit_word":
                    await handle_word_submission(room_id, user_id, user_nickname, msg.get("word", ""))
                    
                elif msg.get("type") == "chat":
                    # 게임 중 채팅
                    chat_message = {
                        "type": "game_chat",
                        "nickname": user_nickname,
                        "message": msg.get("message", ""),
                        "timestamp": datetime.now().isoformat()
                    }
                    await broadcast_to_game(room_id, chat_message)
                    
            except Exception as e:
                logger.error(f"❌ 게임 메시지 처리 오류: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"🎮 게임 퇴장: {user_nickname}")
        
    except Exception as e:
        logger.error(f"❌ 게임 WebSocket 오류: {e}")
        
    finally:
        # 연결 정리
        if room_id in game_connections and user_id in game_connections[room_id]:
            del game_connections[room_id][user_id]
            
        # 플레이어 제거 및 게임 상태 업데이트
        if room_id in game_sessions:
            game_sessions[room_id]["players"] = [
                p for p in game_sessions[room_id]["players"] if p["guest_id"] != user_id
            ]
            
            if not game_sessions[room_id]["players"]:
                # 모든 플레이어가 나가면 게임 세션 삭제
                del game_sessions[room_id]
                if room_id in game_connections:
                    del game_connections[room_id]
            else:
                # 남은 플레이어들에게 퇴장 알림
                updated_game_state = game_sessions[room_id]
                current_player = updated_game_state["players"][updated_game_state["current_player_index"]]
                updated_game_state["current_player"] = current_player
                
                await broadcast_to_game(room_id, {
                    "type": "player_left",
                    "message": f"👋 {user_nickname}님이 게임을 나갔습니다.",
                    "players": updated_game_state["players"],
                    "current_player": current_player,
                    "game_state": updated_game_state,
                    "timestamp": datetime.now().isoformat()
                })

async def handle_word_submission(room_id: int, user_id: str, user_nickname: str, word: str):
    """단어 제출 처리"""
    if room_id not in game_sessions:
        return
    
    game = game_sessions[room_id]
    
    # 현재 턴인지 확인
    current_player = game["players"][game["current_player_index"]]
    if current_player["guest_id"] != user_id:
        await game_connections[room_id][user_id].send_text(json.dumps({
            "type": "error",
            "message": "지금은 당신의 차례가 아닙니다!",
            "timestamp": datetime.now().isoformat()
        }))
        return
    
    # 단어 검증
    word = word.strip()
    if not word:
        await game_connections[room_id][user_id].send_text(json.dumps({
            "type": "error", 
            "message": "단어를 입력해주세요!",
            "timestamp": datetime.now().isoformat()
        }))
        return
    
    # 이미 사용된 단어인지 확인
    if word in game["words_used"]:
        await game_connections[room_id][user_id].send_text(json.dumps({
            "type": "error",
            "message": f"'{word}'는 이미 사용된 단어입니다!",
            "timestamp": datetime.now().isoformat()
        }))
        return
    
    # 끝말잇기 규칙 확인
    if game["last_word"] and not is_valid_word_chain(game["last_word"], word):
        await game_connections[room_id][user_id].send_text(json.dumps({
            "type": "error",
            "message": f"'{game['last_word']}'의 마지막 글자 '{get_last_char(game['last_word'])}'(으)로 시작하는 단어를 입력해주세요!",
            "timestamp": datetime.now().isoformat()
        }))
        return
    
    # 유효한 단어인지 확인 (간단한 검증)
    if word not in KOREAN_WORDS:
        await game_connections[room_id][user_id].send_text(json.dumps({
            "type": "error",
            "message": f"'{word}'는 사전에 없는 단어입니다!",
            "timestamp": datetime.now().isoformat()
        }))
        return
    
    # 단어 승인 및 게임 상태 업데이트
    game["words_used"].append(word)
    game["last_word"] = word
    game["scores"][user_id] += 10  # 간단한 점수 시스템
    
    # 다음 턴으로 이동
    game["current_player_index"] = (game["current_player_index"] + 1) % len(game["players"])
    next_player = game["players"][game["current_player_index"]]
    game["current_player"] = next_player  # 현재 플레이어 정보 업데이트
    
    # 모든 플레이어에게 단어 승인 알림
    await broadcast_to_game(room_id, {
        "type": "word_accepted",
        "word": word,
        "player": user_nickname,
        "player_id": user_id,
        "last_char": get_last_char(word),
        "next_player": next_player["nickname"],
        "next_player_id": next_player["guest_id"],
        "current_player": next_player,
        "scores": game["scores"],
        "words_count": len(game["words_used"]),
        "words_used": game["words_used"],
        "game_state": game,
        "turn_message": f"🎯 {next_player['nickname']}님의 차례입니다!",
        "timestamp": datetime.now().isoformat()
    })
    
    # 게임 종료 조건 확인 (예: 단어가 20개 이상이면 종료)
    if len(game["words_used"]) >= 20:
        await end_game(room_id, "단어 한계 달성")

async def start_game_announcement(room_id: int):
    """게임 시작 안내"""
    if room_id not in game_sessions:
        return
    
    game = game_sessions[room_id]
    game["game_state"] = "playing"  # 게임 상태를 playing으로 변경
    
    current_player = game["players"][game["current_player_index"]]
    start_word = game["start_word"]
    last_char = get_last_char(start_word)
    
    await broadcast_to_game(room_id, {
        "type": "game_started_with_word",
        "message": f"🎮 게임이 시작되었습니다!",
        "start_word": start_word,
        "last_char": last_char,
        "current_player": current_player,
        "next_word_hint": f"'{last_char}'(으)로 시작하는 단어를 입력하세요!",
        "game_state": game,
        "timestamp": datetime.now().isoformat()
    })

async def end_game(room_id: int, reason: str):
    """게임 종료 처리"""
    if room_id not in game_sessions:
        return
    
    game = game_sessions[room_id]
    game["game_state"] = "ended"
    
    # 승자 결정 (점수 기준)
    winner_id = max(game["scores"], key=game["scores"].get)
    winner = next(p for p in game["players"] if p["guest_id"] == winner_id)
    
    # 게임 종료 알림
    await broadcast_to_game(room_id, {
        "type": "game_ended",
        "reason": reason,
        "winner": winner["nickname"],
        "final_scores": game["scores"],
        "total_words": len(game["words_used"]),
        "words_used": game["words_used"],
        "timestamp": datetime.now().isoformat()
    })