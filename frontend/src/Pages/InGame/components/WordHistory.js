import React, { useState } from 'react';

const WordHistory = ({ usedWords = [], players = [] }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // 플레이어별 색상 배열
  const playerColors = [
    'bg-blue-100 text-blue-700 border-blue-300',
    'bg-green-100 text-green-700 border-green-300',
    'bg-yellow-100 text-yellow-700 border-yellow-300',
    'bg-red-100 text-red-700 border-red-300',
    'bg-purple-100 text-purple-700 border-purple-300',
    'bg-pink-100 text-pink-700 border-pink-300',
    'bg-indigo-100 text-indigo-700 border-indigo-300',
    'bg-teal-100 text-teal-700 border-teal-300'
  ];
  
  // 플레이어 인덱스 찾기
  const getPlayerColorClass = (playerName) => {
    const index = players.indexOf(playerName);
    return playerColors[index % playerColors.length];
  };
  
  // 검색어로 필터링
  const filteredWords = usedWords.filter(item => 
    item.word.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.player?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // 표시할 단어 수 결정
  const displayWords = isExpanded ? filteredWords : filteredWords.slice(-10);

  return (
    <div className="w-full bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-800">단어 히스토리</h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">
            총 {usedWords.length}개
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-purple-600 hover:text-purple-700 font-medium transition-colors"
          >
            {isExpanded ? '접기' : '전체보기'}
          </button>
        </div>
      </div>
      
      {/* 검색 바 (확장 시에만 표시) */}
      {isExpanded && (
        <div className="mb-4">
          <input
            type="text"
            placeholder="단어나 플레이어 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 text-sm"
          />
        </div>
      )}
      
      {/* 단어 목록 */}
      <div className={`space-y-2 ${isExpanded ? 'max-h-96 overflow-y-auto' : ''}`}>
        {displayWords.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            {searchTerm ? '검색 결과가 없습니다.' : '아직 사용된 단어가 없습니다.'}
          </div>
        ) : (
          displayWords.map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors animate-fadeIn"
              style={{
                animationDelay: `${index * 0.05}s`
              }}
            >
              {/* 단어 정보 */}
              <div className="flex items-center space-x-3">
                <div className="text-2xl font-bold text-gray-700">
                  {item.word}
                </div>
                {item.player && (
                  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getPlayerColorClass(item.player)}`}>
                    {item.player}
                  </span>
                )}
              </div>
              
              {/* 추가 정보 */}
              <div className="flex items-center space-x-3 text-sm text-gray-500">
                {item.timestamp && (
                  <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                )}
                <span className="text-gray-400">#{usedWords.length - index}</span>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* 단어 체인 미리보기 (축소 시) */}
      {!isExpanded && usedWords.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-1 overflow-x-auto pb-2">
            {usedWords.slice(-5).map((item, index) => (
              <React.Fragment key={index}>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium whitespace-nowrap">
                  {item.word}
                </span>
                {index < usedWords.slice(-5).length - 1 && (
                  <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
      
      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateX(-10px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default WordHistory;