"""
게임 모드 관리 서비스
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.game_mode_model import GameMode, DEFAULT_GAME_MODES
from schemas.game_mode_schema import (
    GameModeCreate, GameModeUpdate, GameModeResponse,
    GameRoomModeRequest, GameModeValidationResponse
)
import logging

logger = logging.getLogger(__name__)


class GameModeService:
    """게임 모드 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_default_modes(self) -> bool:
        """기본 게임 모드들을 데이터베이스에 초기화"""
        try:
            for mode_data in DEFAULT_GAME_MODES:
                existing = self.db.query(GameMode).filter(
                    GameMode.name == mode_data["name"]
                ).first()
                
                if not existing:
                    game_mode = GameMode(**mode_data)
                    self.db.add(game_mode)
                    logger.info(f"기본 게임 모드 생성: {mode_data['name']}")
            
            self.db.commit()
            logger.info("기본 게임 모드 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"기본 게임 모드 초기화 실패: {e}")
            self.db.rollback()
            return False
    
    def get_all_modes(self, active_only: bool = True) -> List[GameModeResponse]:
        """모든 게임 모드 조회"""
        try:
            query = self.db.query(GameMode)
            
            if active_only:
                query = query.filter(GameMode.is_active == True)
            
            modes = query.order_by(GameMode.is_default.desc(), GameMode.name).all()
            return [GameModeResponse.from_orm(mode) for mode in modes]
            
        except Exception as e:
            logger.error(f"게임 모드 목록 조회 실패: {e}")
            return []
    
    def get_mode_by_name(self, name: str) -> Optional[GameModeResponse]:
        """이름으로 게임 모드 조회"""
        try:
            mode = self.db.query(GameMode).filter(
                and_(GameMode.name == name, GameMode.is_active == True)
            ).first()
            
            if mode:
                return GameModeResponse.from_orm(mode)
            return None
            
        except Exception as e:
            logger.error(f"게임 모드 조회 실패 (name: {name}): {e}")
            return None
    
    def get_mode_by_id(self, mode_id: int) -> Optional[GameModeResponse]:
        """ID로 게임 모드 조회"""
        try:
            mode = self.db.query(GameMode).filter(
                and_(GameMode.mode_id == mode_id, GameMode.is_active == True)
            ).first()
            
            if mode:
                return GameModeResponse.from_orm(mode)
            return None
            
        except Exception as e:
            logger.error(f"게임 모드 조회 실패 (id: {mode_id}): {e}")
            return None
    
    def get_default_mode(self) -> Optional[GameModeResponse]:
        """기본 게임 모드 조회"""
        try:
            mode = self.db.query(GameMode).filter(
                and_(GameMode.is_default == True, GameMode.is_active == True)
            ).first()
            
            if mode:
                return GameModeResponse.from_orm(mode)
            
            # 기본 모드가 없으면 첫 번째 활성 모드 반환
            mode = self.db.query(GameMode).filter(
                GameMode.is_active == True
            ).first()
            
            if mode:
                return GameModeResponse.from_orm(mode)
            
            return None
            
        except Exception as e:
            logger.error(f"기본 게임 모드 조회 실패: {e}")
            return None
    
    def create_mode(self, mode_data: GameModeCreate) -> Optional[GameModeResponse]:
        """새 게임 모드 생성"""
        try:
            # 이름 중복 체크
            existing = self.db.query(GameMode).filter(
                GameMode.name == mode_data.name
            ).first()
            
            if existing:
                logger.warning(f"게임 모드 이름 중복: {mode_data.name}")
                return None
            
            game_mode = GameMode(**mode_data.dict())
            self.db.add(game_mode)
            self.db.commit()
            self.db.refresh(game_mode)
            
            logger.info(f"게임 모드 생성 완료: {mode_data.name}")
            return GameModeResponse.from_orm(game_mode)
            
        except Exception as e:
            logger.error(f"게임 모드 생성 실패: {e}")
            self.db.rollback()
            return None
    
    def update_mode(self, mode_id: int, mode_data: GameModeUpdate) -> Optional[GameModeResponse]:
        """게임 모드 업데이트"""
        try:
            mode = self.db.query(GameMode).filter(GameMode.mode_id == mode_id).first()
            
            if not mode:
                return None
            
            # 업데이트할 필드만 적용
            update_data = mode_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(mode, field, value)
            
            self.db.commit()
            self.db.refresh(mode)
            
            logger.info(f"게임 모드 업데이트 완료: {mode.name}")
            return GameModeResponse.from_orm(mode)
            
        except Exception as e:
            logger.error(f"게임 모드 업데이트 실패: {e}")
            self.db.rollback()
            return None
    
    def validate_mode_for_room(self, request: GameRoomModeRequest) -> GameModeValidationResponse:
        """게임방에서 사용할 모드 설정 검증"""
        try:
            mode = self.get_mode_by_name(request.mode_name)
            
            if not mode:
                return GameModeValidationResponse(
                    is_valid=False,
                    validation_errors=[f"게임 모드를 찾을 수 없습니다: {request.mode_name}"]
                )
            
            # 유효한 설정 계산
            effective_settings = self._calculate_effective_settings(mode, request.custom_settings)
            
            # 설정 검증
            validation_errors = []
            warnings = []
            
            # 시간 제한 검증
            if effective_settings['turn_time_limit'] < 5:
                validation_errors.append("턴 제한 시간은 최소 5초 이상이어야 합니다")
            elif effective_settings['turn_time_limit'] > 300:
                validation_errors.append("턴 제한 시간은 최대 300초 이하여야 합니다")
            
            # 라운드 수 검증
            if effective_settings['max_rounds'] < 1:
                validation_errors.append("라운드 수는 최소 1라운드 이상이어야 합니다")
            elif effective_settings['max_rounds'] > 50:
                validation_errors.append("라운드 수는 최대 50라운드 이하여야 합니다")
            
            # 단어 길이 검증
            if effective_settings['min_word_length'] >= effective_settings['max_word_length']:
                validation_errors.append("최소 단어 길이는 최대 단어 길이보다 작아야 합니다")
            
            # 경고 메시지
            if effective_settings['turn_time_limit'] <= 10:
                warnings.append("매우 짧은 턴 시간으로 게임이 매우 빨라질 수 있습니다")
            
            if effective_settings['max_rounds'] >= 20:
                warnings.append("많은 라운드로 게임이 매우 길어질 수 있습니다")
            
            return GameModeValidationResponse(
                is_valid=len(validation_errors) == 0,
                mode=mode,
                effective_settings=effective_settings,
                validation_errors=validation_errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"게임 모드 검증 실패: {e}")
            return GameModeValidationResponse(
                is_valid=False,
                validation_errors=["게임 모드 검증 중 오류가 발생했습니다"]
            )
    
    def _calculate_effective_settings(self, mode: GameModeResponse, custom_settings: Dict[str, Any]) -> Dict[str, Any]:
        """모드 설정과 커스텀 설정을 합쳐서 최종 설정 계산"""
        effective = {
            'turn_time_limit': mode.turn_time_limit,
            'max_rounds': mode.max_rounds,
            'min_word_length': mode.min_word_length,
            'max_word_length': mode.max_word_length,
            'score_multiplier': mode.score_multiplier,
            'enable_advanced_scoring': mode.enable_advanced_scoring,
            'special_rules': mode.special_rules.copy(),
        }
        
        # 커스텀 설정으로 오버라이드
        if custom_settings:
            for key, value in custom_settings.items():
                if key in effective and value is not None:
                    effective[key] = value
        
        return effective
    
    def get_mode_statistics(self) -> Dict[str, Any]:
        """게임 모드 통계 조회"""
        try:
            total_modes = self.db.query(GameMode).count()
            active_modes = self.db.query(GameMode).filter(GameMode.is_active == True).count()
            default_mode = self.db.query(GameMode).filter(GameMode.is_default == True).first()
            
            return {
                'total_modes': total_modes,
                'active_modes': active_modes,
                'inactive_modes': total_modes - active_modes,
                'default_mode_name': default_mode.name if default_mode else None,
                'available_modes': [mode.name for mode in self.get_all_modes()]
            }
            
        except Exception as e:
            logger.error(f"게임 모드 통계 조회 실패: {e}")
            return {}