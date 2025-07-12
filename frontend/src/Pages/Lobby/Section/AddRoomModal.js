import React, { useState, useEffect } from 'react';
import Modal from 'react-modal';
import './AddRoomModal.css';
import axiosInstance from '../../../Api/axiosInstance';
import { gameLobbyUrl } from '../../../utils/urls';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { getErrorMessage, SUCCESS_MESSAGES } from '../../../utils/errorMessages';

Modal.setAppElement('#root');

function AddRoomModal({ isOpen, isClose }) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [roomTitle, setRoomTitle] = useState('');
  const [maxPlayers, setMaxPlayers] = useState(2);
  const [gameMode, setGameMode] = useState('arcade');
  const [timeLimit] = useState(120);
  const [maxRounds, setMaxRounds] = useState(10);
  const [isCreating, setIsCreating] = useState(false);
  const [errors, setErrors] = useState({});
  const [isValid, setIsValid] = useState(false);

  // 실시간 유효성 검사
  useEffect(() => {
    const validateForm = () => {
      const newErrors = {};
      
      if (!roomTitle.trim()) {
        newErrors.title = '방 제목을 입력해주세요';
      } else if (roomTitle.trim().length < 2) {
        newErrors.title = '방 제목은 2자 이상이어야 합니다';
      } else if (roomTitle.trim().length > 20) {
        newErrors.title = '방 제목은 20자 이하여야 합니다';
      }
      
      if (!gameMode) {
        newErrors.gameMode = '게임 모드를 선택해주세요';
      }
      
      setErrors(newErrors);
      setIsValid(Object.keys(newErrors).length === 0 && roomTitle.trim().length >= 2);
    };
    
    validateForm();
  }, [roomTitle, gameMode]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isValid || isCreating) {
      return;
    }

    // 인증 상태 확인
    if (!isAuthenticated) {
      alert('로그인이 필요합니다');
      navigate('/');
      return;
    }

    try {
      setIsCreating(true);
      setErrors({});
      
      const response = await axiosInstance.post('/gamerooms/', {
        title: roomTitle.trim(),
        max_players: maxPlayers,
        game_mode: gameMode,
        time_limit: timeLimit,
        max_rounds: maxRounds,
      });

      // 성공 처리
      isClose(false);
      setRoomTitle('');
      navigate(gameLobbyUrl(response.data.room_id));
    } catch (error) {
      console.error('방 생성 오류:', error);
      
      const errorMessage = getErrorMessage(error);
      setErrors({ submit: errorMessage });
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    if (!isCreating) {
      setRoomTitle('');
      setErrors({});
      isClose(false);
    }
  };

  return (
    <div className="modal-app">
      <Modal
        isOpen={isOpen}
        onRequestClose={() => isClose(false)}
        contentLabel="Add Room Modal"
        style={{
          overlay: { backgroundColor: 'rgba(0, 0, 0, 0.5)' },
          content: { border: 'none', background: 'none', padding: 0 },
        }}
      >
        <div className="modal-container">
          <div className="modal-ears">
            <div className="ear left"></div>
            <div className="ear right"></div>
          </div>
          <div className="modal-content">
            <button className="close-btn" onClick={() => isClose(false)}>
              ×
            </button>
            <h2 className="modal-title">끄아 방 만들기</h2>

            {/* 전체 에러 메시지 */}
            {errors.submit && (
              <div className="error-message submit-error">
                {errors.submit}
              </div>
            )}

            {/* 방 제목 입력 */}
            <div className="input-group">
              <input
                type="text"
                placeholder="방 제목 (2-20자)"
                value={roomTitle}
                onChange={(e) => setRoomTitle(e.target.value)}
                className={`room-title-input ${errors.title ? 'error' : ''}`}
                disabled={isCreating}
                maxLength={20}
              />
              {errors.title && (
                <div className="error-message">
                  {errors.title}
                </div>
              )}
            </div>

            {/* 게임 설정 */}
            <div className="game-settings">
              <div className="game-mode-section">
                <div className="label">게임 모드</div>
                <div className="mode-buttons">
                  <button
                    className={`mode-btn active`}
                    onClick={() => setGameMode('arcade')}
                  >
                    아케이드
                  </button>
                  <button
                    className={`mode-btn boss`}
                    onClick={() => alert('wating for Update v0.2 ~')}
                  >
                    보스전
                  </button>
                </div>
              </div>

              <div className="game-size-section">
                <div className="label">인원</div>
                <div className="size-buttons">
                  {[2, 3, 4].map((num) => (
                    <label key={num}>
                      <input
                        type="radio"
                        name="size"
                        value={num}
                        checked={maxPlayers === num}
                        onChange={() => setMaxPlayers(num)}
                      />{' '}
                      {num}인
                    </label>
                  ))}
                </div>
              </div>

              <div className="game-rounds-section">
                <div className="label">라운드 수</div>
                <div className="rounds-controls">
                  <div className="rounds-slider">
                    <input
                      type="range"
                      min="5"
                      max="20"
                      step="1"
                      value={maxRounds}
                      onChange={(e) => setMaxRounds(parseInt(e.target.value))}
                      className="slider"
                      disabled={isCreating}
                    />
                    <div className="rounds-display">
                      <span className="rounds-value">{maxRounds}</span>
                      <span className="rounds-text">라운드</span>
                    </div>
                  </div>
                  <div className="rounds-presets">
                    {[5, 10, 15, 20].map((rounds) => (
                      <button
                        key={rounds}
                        className={`preset-btn ${maxRounds === rounds ? 'active' : ''}`}
                        onClick={() => setMaxRounds(rounds)}
                        disabled={isCreating}
                        type="button"
                      >
                        {rounds}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 생성 버튼 */}
            <button
              className={isValid && !isCreating ? 'create-btn' : 'create-btn-fasle'}
              onClick={handleSubmit}
              disabled={!isValid || isCreating}
            >
              {isCreating ? (
                <>
                  <span className="loading-spinner"></span>
                  생성 중...
                </>
              ) : (
                '생성하기'
              )}
            </button>
            <button 
              className="cancel-btn" 
              onClick={handleClose}
              disabled={isCreating}
            >
              취소하기
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default AddRoomModal;
