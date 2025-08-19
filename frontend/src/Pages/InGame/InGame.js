import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import GameLayout from './components/GameLayout';
import GameControls from './components/GameControls';
import GameResultModal from './components/GameResultModal';
import useWordChain from './hooks/useWordChain';
import axiosInstance from '../../Api/axiosInstance';
import { ROOM_API } from '../../Api/roomApi';
import { useAuth } from '../../contexts/AuthContext';

function InGame() {
  const { gameid } = useParams();
  const { user } = useAuth();
  const [showResultModal, setShowResultModal] = useState(false);
  const [gameResultData, setGameResultData] = useState(null);

  const {
    gameState,
    inputWord,
    isMyTurn,
    errorMessage,
    connected: wsConnected,
    isReconnecting,
    connectionAttempts,
    maxReconnectAttempts,
    participants: wsParticipants,
    manualReconnect,
    handleInputChange,
    handleKeyPress,
    submitWord,
  } = useWordChain();

  const handleClickFinish = async () => {
    // 방장인지 확인
    const isOwner = wsParticipants.some(
      (p) => p.guest_id === user?.guest_id && p.is_creator
    );

    if (!isOwner) {
      alert('방장만 게임을 종료할 수 있습니다.');
      return;
    }

    const confirmEnd = window.confirm('정말로 게임을 종료하시겠습니까?');
    if (!confirmEnd) {
      return;
    }

    try {
      await axiosInstance.post(ROOM_API.END_ROOMS(gameid));

      // WebSocket 메시지에서 페이지 이동을 처리하므로 여기서는 추가 처리 불필요
    } catch (error) {
      console.error('게임 종료 실패:', error);

      let errorMessage = '게임 종료 중 오류가 발생했습니다.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      alert(errorMessage);
    }
  };

  const handleClickComplete = async () => {
    const confirmComplete = window.confirm(
      '게임을 완료하시겠습니까? 결과 모달이 표시됩니다.'
    );
    if (!confirmComplete) {
      return;
    }

    try {
      const response = await axiosInstance.post(
        ROOM_API.COMPLETE_ROOMS(gameid)
      );

      // 게임 완료 응답 데이터 저장
      if (response.data.winner) {
        setGameResultData({
          winner_name: response.data.winner,
          status: response.data.status,
        });
      }

      // WebSocket 메시지에서 모달 표시 처리
      // (useGameRoomSocket에서 game_completed 이벤트로 처리될 예정)
    } catch (error) {
      console.error('게임 완료 실패:', error);

      let errorMessage = '게임 완료 중 오류가 발생했습니다.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.status === 403) {
        errorMessage = '게임 참가자만 완료할 수 있습니다.';
      } else if (error.response?.status === 400) {
        errorMessage = '진행 중인 게임만 완료할 수 있습니다.';
      }

      alert(errorMessage);
    }
  };

  const handleCloseResultModal = () => {
    setShowResultModal(false);
    setGameResultData(null);
  };


  // WebSocket 게임 완료 이벤트 콜백 설정
  useEffect(() => {
    window.gameCompletedCallback = (data) => {
      setGameResultData({
        winner_name: data.winner_nickname,
        winner_id: data.winner_id,
        room_id: data.room_id,
        completed_by: data.completed_by_nickname,
      });
      setShowResultModal(true);
    };

    return () => {
      // 컴포넌트 언마운트 시 콜백 정리
      window.gameCompletedCallback = null;
    };
  }, []);

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="max-w-7xl mx-auto p-4">
          <div className="grid grid-cols-1 gap-6">
            {/* 메인 게임 영역 */}
            <div>
              <GameLayout
                gameState={gameState}
                inputWord={inputWord}
                isMyTurn={isMyTurn}
                errorMessage={errorMessage}
                wsConnected={wsConnected}
                isReconnecting={isReconnecting}
                connectionAttempts={connectionAttempts}
                maxReconnectAttempts={maxReconnectAttempts}
                manualReconnect={manualReconnect}
                wsParticipants={wsParticipants}
                handleInputChange={handleInputChange}
                handleKeyPress={handleKeyPress}
                submitWord={submitWord}
              />

              <GameControls
                handleClickFinish={handleClickFinish}
                handleClickComplete={handleClickComplete}
              />
            </div>

          </div>
        </div>


      </div>

      {/* 게임 결과 모달 */}
      <GameResultModal
        isOpen={showResultModal}
        onClose={handleCloseResultModal}
        roomId={gameid}
        winnerData={gameResultData}
      />
    </>
  );
}

export default InGame;
