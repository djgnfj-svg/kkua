"""
게임 플레이 관련 API 라우터
Redis 기반 실시간 게임 로직 처리
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from db.postgres import get_db
from models.guest_model import Guest
from middleware.auth_middleware import require_authentication
from services.redis_game_service import get_redis_game_service


router = APIRouter(prefix="/api/game", tags=["game"])


class WordSubmissionRequest(BaseModel):
    word: str


class GameStateResponse(BaseModel):
    room_id: int
    status: str
    current_player_id: Optional[int]
    current_player_nickname: Optional[str]
    last_word: str
    last_character: str
    time_left: int
    round_number: int
    max_rounds: int
    used_words: List[str]


class PlayerStatsResponse(BaseModel):
    guest_id: int
    nickname: str
    score: int
    words_submitted: int
    status: str


@router.post("/{room_id}/submit-word")
async def submit_word(
    room_id: int,
    request: WordSubmissionRequest,
    guest: Guest = Depends(require_authentication)
):
    """단어 제출"""
    try:
        redis_game = await get_redis_game_service()
        result = await redis_game.submit_word(room_id, guest.guest_id, request.word)
        
        if result['success']:
            # WebSocket 브로드캐스트
            from services.gameroom_service import ws_manager
            
            if result.get('game_over'):
                # 게임 종료 브로드캐스트
                await ws_manager.broadcast_to_room(room_id, {
                    'type': 'game_over',
                    'room_id': room_id,
                    'winner_id': guest.guest_id,
                    'winner_nickname': guest.nickname,
                    'final_word': request.word,
                    'reason': result.get('game_over_reason', ''),
                    'message': '게임이 종료되었습니다!'
                })
            else:
                # 단어 제출 성공 브로드캐스트
                await ws_manager.broadcast_to_room(room_id, {
                    'type': 'word_submitted',
                    'word': request.word,
                    'submitted_by_id': guest.guest_id,
                    'submitted_by_nickname': guest.nickname,
                    'next_player_id': result['next_player_id'],
                    'last_character': result['last_character'],
                    'current_round': result['current_round'],
                    'max_rounds': result['max_rounds'],
                    'time_left': result['time_left']
                })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"단어 제출 처리 중 오류: {str(e)}"
        )


@router.get("/{room_id}/state", response_model=GameStateResponse)
async def get_game_state(
    room_id: int,
    guest: Guest = Depends(require_authentication)
):
    """게임 상태 조회"""
    try:
        redis_game = await get_redis_game_service()
        game_state = await redis_game.get_game_state(room_id)
        
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임을 찾을 수 없습니다."
            )
        
        # 현재 플레이어 닉네임 찾기
        current_player_nickname = None
        if game_state['current_player_id']:
            for participant in game_state['participants']:
                if participant['guest_id'] == game_state['current_player_id']:
                    current_player_nickname = participant['nickname']
                    break
        
        return GameStateResponse(
            room_id=room_id,
            status=game_state['status'],
            current_player_id=game_state['current_player_id'],
            current_player_nickname=current_player_nickname,
            last_word=game_state['last_word'],
            last_character=game_state['last_character'],
            time_left=game_state['time_left'],
            round_number=game_state['round_number'],
            max_rounds=game_state['game_settings']['max_rounds'],
            used_words=game_state['used_words']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"게임 상태 조회 중 오류: {str(e)}"
        )


@router.get("/{room_id}/stats", response_model=List[PlayerStatsResponse])
async def get_player_stats(
    room_id: int,
    guest: Guest = Depends(require_authentication)
):
    """플레이어 통계 조회"""
    try:
        redis_game = await get_redis_game_service()
        stats = await redis_game.get_all_player_stats(room_id)
        
        return [
            PlayerStatsResponse(
                guest_id=stat['guest_id'],
                nickname=stat['nickname'],
                score=stat['score'],
                words_submitted=stat['words_submitted'],
                status=stat['status']
            )
            for stat in stats
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"플레이어 통계 조회 중 오류: {str(e)}"
        )


@router.post("/{room_id}/end")
async def end_game(
    room_id: int,
    guest: Guest = Depends(require_authentication)
):
    """게임 종료 (방장만 가능)"""
    try:
        redis_game = await get_redis_game_service()
        game_state = await redis_game.get_game_state(room_id)
        
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임을 찾을 수 없습니다."
            )
        
        # 방장 확인
        is_creator = False
        for participant in game_state['participants']:
            if participant['guest_id'] == guest.guest_id and participant['is_creator']:
                is_creator = True
                break
        
        if not is_creator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="방장만 게임을 종료할 수 있습니다."
            )
        
        # 게임 종료
        success = await redis_game.end_game(room_id)
        
        if success:
            # WebSocket 브로드캐스트
            from services.gameroom_service import ws_manager
            await ws_manager.broadcast_to_room(room_id, {
                'type': 'game_ended_by_host',
                'room_id': room_id,
                'ended_by_id': guest.guest_id,
                'ended_by_nickname': guest.nickname,
                'message': '방장이 게임을 종료했습니다.'
            })
            
            return {"message": "게임이 종료되었습니다."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="게임 종료에 실패했습니다."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"게임 종료 처리 중 오류: {str(e)}"
        )