import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function InGameSimple() {
  const { gameid } = useParams();
  const navigate = useNavigate();
  
  // 게임 상태
  const [connected, setConnected] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [players, setPlayers] = useState([]);
  const [wordsUsed, setWordsUsed] = useState([]);
  const [currentWord, setCurrentWord] = useState('');
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [lastChar, setLastChar] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [scores, setScores] = useState({});
  const [gameEnded, setGameEnded] = useState(false);
  const [winner, setWinner] = useState('');
  const [currentPlayer, setCurrentPlayer] = useState(null);
  const [gameStarted, setGameStarted] = useState(false);
  const [startWord, setStartWord] = useState('');
  const [myPlayerId, setMyPlayerId] = useState(null);
  
  // WebSocket 관련
  const socketRef = useRef(null);
  const inputRef = useRef(null);
  
  // WebSocket 연결
  useEffect(() => {
    if (!gameid) return;

    const wsUrl = `ws://localhost:8000/ws/game/rooms/${gameid}`;
    console.log('🎮 게임 WebSocket 연결:', wsUrl);

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('✅ 게임 연결 성공!');
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 게임 메시지:', data);
      
      handleWebSocketMessage(data);
    };

    socket.onerror = (error) => {
      console.error('❌ 게임 연결 오류:', error);
    };

    socket.onclose = () => {
      console.log('🔌 게임 연결 종료');
      setConnected(false);
    };

    socketRef.current = socket;

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [gameid]);

  // WebSocket 메시지 처리
  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'game_joined':
        const gameState = data.game_state;
        const myPlayer = gameState.players.find(p => data.your_turn && p.guest_id === data.current_player?.guest_id);
        
        setGameState(gameState);
        setPlayers(gameState.players || []);
        setWordsUsed(gameState.words_used || []);
        setLastChar(gameState.last_word ? gameState.last_word.slice(-1) : '');
        setIsMyTurn(data.your_turn);
        setScores(gameState.scores || {});
        setCurrentPlayer(data.current_player);
        
        // 내 플레이어 ID 저장 (추정)
        if (data.your_turn && data.current_player) {
          setMyPlayerId(data.current_player.guest_id);
        }
        
        // 게임 시작 여부 확인
        if (gameState.game_state === 'playing') {
          setGameStarted(true);
          setStartWord(gameState.start_word || gameState.last_word);
        }
        break;
        
      case 'player_joined':
        setPlayers(data.players);
        if (data.current_player) {
          setCurrentPlayer(data.current_player);
        }
        break;
        
      case 'game_started_with_word':
        setGameStarted(true);
        setStartWord(data.start_word);
        setLastChar(data.last_char);
        setCurrentPlayer(data.current_player);
        setGameState(data.game_state);
        // 내가 첫 번째 플레이어인지 확인
        if (data.current_player && !myPlayerId) {
          // 첫 번째 메시지로 내 ID 추정
          setMyPlayerId(data.current_player.guest_id);
          setIsMyTurn(true);
        }
        break;
        
      case 'word_accepted':
        setWordsUsed(data.words_used || [...wordsUsed, data.word]);
        setLastChar(data.last_char);
        setScores(data.scores);
        setErrorMessage('');
        setCurrentWord('');
        setCurrentPlayer(data.current_player);
        setGameState(data.game_state);
        
        // 턴 상태 업데이트
        if (myPlayerId) {
          setIsMyTurn(data.current_player?.guest_id === myPlayerId);
        }
        
        // 내 턴이면 입력창에 포커스
        if (data.current_player?.guest_id === myPlayerId) {
          setTimeout(() => {
            if (inputRef.current) {
              inputRef.current.focus();
            }
          }, 100);
        }
        break;
        
      case 'game_chat':
        // 채팅은 단순하게 콘솔에만 표시
        console.log(`💬 ${data.nickname}: ${data.message}`);
        break;
        
      case 'game_ended':
        setGameEnded(true);
        setWinner(data.winner);
        setTimeout(() => {
          navigate('/lobby');
        }, 5000);
        break;
        
      case 'error':
        setErrorMessage(data.message);
        setTimeout(() => setErrorMessage(''), 3000);
        break;
        
      default:
        console.log('🤔 알 수 없는 게임 메시지:', data);
    }
  };

  // 단어 제출
  const handleSubmitWord = () => {
    if (!currentWord.trim() || !socketRef.current || !isMyTurn) return;

    socketRef.current.send(JSON.stringify({
      type: 'submit_word',
      word: currentWord.trim(),
      timestamp: new Date().toISOString()
    }));
  };

  // 엔터키 처리
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmitWord();
    }
  };

  // 연결 대기 중
  if (!connected) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="text-4xl mb-4">🎮</div>
          <div className="text-xl font-bold animate-pulse">게임 접속 중...</div>
        </div>
      </div>
    );
  }

  // 게임 시작 대기 중
  if (connected && !gameStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 text-center text-white border border-white/20">
          <div className="text-4xl mb-4">⏳</div>
          <h1 className="text-2xl font-bold mb-4">게임 준비 중...</h1>
          <p className="text-white/80 mb-4">다른 플레이어를 기다리고 있습니다</p>
          <div className="space-y-2">
            {players.map((player, index) => (
              <div key={player.guest_id} className="text-white/60">
                👤 {player.nickname} 
                {currentPlayer?.guest_id === player.guest_id && <span className="text-yellow-300 ml-2">🎯 첫 번째</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 게임 종료
  if (gameEnded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 text-center text-white border border-white/20">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-3xl font-bold mb-4">게임 종료!</h1>
          <p className="text-xl mb-4">🏆 승자: <span className="text-yellow-300 font-bold">{winner}</span></p>
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">최종 점수:</h3>
            {Object.entries(scores).map(([playerId, score]) => {
              const player = players.find(p => p.guest_id === playerId);
              return (
                <div key={playerId} className="text-white/80">
                  {player?.nickname || playerId}: {score}점
                </div>
              );
            })}
          </div>
          <p className="text-sm text-white/60">5초 후 로비로 이동합니다...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 via-blue-900 to-purple-900 p-4">
      <div className="max-w-6xl mx-auto">
        
        {/* 헤더 */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 mb-6 border border-white/20">
          <h1 className="text-3xl font-bold text-white mb-2">🎮 끝말잇기 게임</h1>
          <p className="text-white/80">방 번호: {gameid}</p>
          {startWord && (
            <div className="mt-3 text-center">
              <span className="bg-blue-500/30 px-3 py-1 rounded-lg text-white">
                시작 단어: <span className="font-bold text-yellow-300">{startWord}</span>
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* 게임 영역 */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 mb-6">
              <h2 className="text-xl font-bold text-white mb-4">🎯 현재 상황</h2>
              
              {lastChar && (
                <div className="bg-yellow-500/20 rounded-lg p-4 mb-4">
                  <p className="text-white text-center">
                    <span className="text-2xl font-bold text-yellow-300">"{lastChar}"</span>
                    (으)로 시작하는 단어를 입력하세요!
                  </p>
                </div>
              )}
              
              <div className="flex gap-4 mb-4">
                <input
                  ref={inputRef}
                  type="text"
                  value={currentWord}
                  onChange={(e) => setCurrentWord(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={isMyTurn ? "단어를 입력하세요..." : "상대방의 차례입니다..."}
                  disabled={!isMyTurn}
                  className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSubmitWord}
                  disabled={!isMyTurn || !currentWord.trim()}
                  className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
                >
                  제출
                </button>
              </div>
              
              {errorMessage && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-4">
                  <p className="text-red-300 text-center">{errorMessage}</p>
                </div>
              )}
              
              <div className="text-center">
                <p className="text-white/80">
                  {isMyTurn 
                    ? "🎯 당신의 차례입니다!" 
                    : `⏳ ${currentPlayer?.nickname || '상대방'}님의 차례를 기다리세요...`
                  }
                </p>
              </div>
            </div>
          </div>

          {/* 사이드바 */}
          <div className="space-y-6">
            
            {/* 플레이어 목록 */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <h3 className="text-lg font-bold text-white mb-4">👥 플레이어</h3>
              {players.map((player, index) => {
                const isCurrentPlayer = currentPlayer?.guest_id === player.guest_id;
                const isMe = myPlayerId === player.guest_id;
                
                return (
                  <div 
                    key={player.guest_id} 
                    className={`flex justify-between items-center py-3 px-3 rounded-lg mb-2 border-b border-white/10 last:border-b-0 transition-all ${
                      isCurrentPlayer 
                        ? 'bg-yellow-500/20 border-yellow-500/50' 
                        : 'hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-white">
                        {isMe && '👤'} {player.nickname}
                        {isCurrentPlayer && (
                          <span className="text-yellow-300 ml-2 text-sm font-semibold animate-pulse">
                            🎯 현재 턴
                          </span>
                        )}
                      </span>
                    </div>
                    <span className="text-yellow-300 font-bold">{scores[player.guest_id] || 0}점</span>
                  </div>
                );
              })}
            </div>

            {/* 사용된 단어들 */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <h3 className="text-lg font-bold text-white mb-4">📝 사용된 단어 ({wordsUsed.length}개)</h3>
              <div className="max-h-64 overflow-y-auto">
                {wordsUsed.length === 0 ? (
                  <p className="text-white/60 text-center">아직 사용된 단어가 없습니다</p>
                ) : (
                  <div className="space-y-2">
                    {wordsUsed.map((word, index) => (
                      <div key={index} className="bg-white/5 rounded px-3 py-1">
                        <span className="text-white/80 text-sm">{index + 1}. </span>
                        <span className="text-white">{word}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 게임 컨트롤 */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <button
                onClick={() => navigate('/lobby')}
                className="w-full px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-colors"
              >
                🚪 게임 나가기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default InGameSimple;