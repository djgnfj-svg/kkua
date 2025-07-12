import React from 'react';

const ItemCards = ({ itemList = [], showCount = 3, onItemUse }) => {
  // 아이템 타입별 설정
  const itemTypes = {
    default: {
      bgColor: 'bg-gradient-to-br from-blue-100 to-blue-200',
      borderColor: 'border-blue-300',
      textColor: 'text-blue-800',
      icon: '📝'
    },
    special: {
      bgColor: 'bg-gradient-to-br from-purple-100 to-purple-200',
      borderColor: 'border-purple-300',
      textColor: 'text-purple-800',
      icon: '✨'
    },
    bonus: {
      bgColor: 'bg-gradient-to-br from-yellow-100 to-yellow-200',
      borderColor: 'border-yellow-300',
      textColor: 'text-yellow-800',
      icon: '🎁'
    },
    power: {
      bgColor: 'bg-gradient-to-br from-red-100 to-red-200',
      borderColor: 'border-red-300',
      textColor: 'text-red-800',
      icon: '⚡'
    }
  };

  // 아이템의 타입 결정 (단어 길이 기준)
  const getItemType = (word) => {
    if (word.length >= 5) return 'power';
    if (word.length >= 4) return 'bonus';
    if (word.length >= 3) return 'special';
    return 'default';
  };

  // 표시할 아이템 결정
  const displayItems = itemList.slice(0, showCount);

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-800">아이템 카드</h3>
        <span className="text-sm text-gray-600">
          {displayItems.length}/{itemList.length}개 표시
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayItems.length === 0 ? (
          <div className="col-span-full text-center py-8 text-gray-500">
            아직 사용 가능한 아이템이 없습니다.
          </div>
        ) : (
          displayItems.map((item, index) => {
            const itemType = getItemType(item.word || '');
            const typeConfig = itemTypes[itemType];
            
            return (
              <div
                key={index}
                className={`relative p-4 rounded-2xl border-2 ${typeConfig.bgColor} ${typeConfig.borderColor} hover:shadow-lg transform hover:scale-105 transition-all duration-300 cursor-pointer animate-fadeIn`}
                style={{
                  animationDelay: `${index * 0.1}s`
                }}
                onClick={() => onItemUse && onItemUse(item, index)}
              >
                {/* 아이템 타입 아이콘 */}
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-white rounded-full shadow-md flex items-center justify-center text-lg">
                  {typeConfig.icon}
                </div>
                
                {/* 아이템 정보 */}
                <div className="text-center">
                  <div className={`text-2xl font-bold ${typeConfig.textColor} mb-2`}>
                    {item.word || '아이템'}
                  </div>
                  
                  {/* 아이템 설명 */}
                  <div className="text-sm text-gray-600 mb-3">
                    {item.description || '특별한 효과가 있는 단어입니다.'}
                  </div>
                  
                  {/* 아이템 효과 */}
                  <div className={`text-xs ${typeConfig.textColor} font-medium`}>
                    {itemType === 'power' && '강력한 효과!'}
                    {itemType === 'bonus' && '보너스 점수'}
                    {itemType === 'special' && '특수 효과'}
                    {itemType === 'default' && '기본 아이템'}
                  </div>
                  
                  {/* 사용 가능 횟수 */}
                  {item.uses && (
                    <div className="mt-2 text-xs text-gray-500">
                      사용 가능: {item.uses}회
                    </div>
                  )}
                </div>
                
                {/* 사용 버튼 */}
                {onItemUse && (
                  <div className="mt-3">
                    <button className={`w-full py-2 px-3 rounded-lg text-white font-medium text-sm transition-colors ${
                      itemType === 'power' ? 'bg-red-500 hover:bg-red-600' :
                      itemType === 'bonus' ? 'bg-yellow-500 hover:bg-yellow-600' :
                      itemType === 'special' ? 'bg-purple-500 hover:bg-purple-600' :
                      'bg-blue-500 hover:bg-blue-600'
                    }`}>
                      사용하기
                    </button>
                  </div>
                )}
                
                {/* 반짝이는 효과 */}
                <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none">
                  <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white to-transparent opacity-20 transform -skew-x-12 animate-shimmer" />
                </div>
              </div>
            );
          })
        )}
      </div>
      
      {/* 더 많은 아이템이 있을 때 힌트 */}
      {itemList.length > showCount && (
        <div className="text-center mt-4">
          <div className="text-sm text-gray-500">
            +{itemList.length - showCount}개의 아이템이 더 있습니다
          </div>
          <div className="flex justify-center space-x-1 mt-2">
            {Array.from({ length: Math.min(3, itemList.length - showCount) }).map((_, i) => (
              <div key={i} className="w-2 h-2 bg-gray-300 rounded-full animate-pulse" />
            ))}
          </div>
        </div>
      )}
      
      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes shimmer {
          0% {
            transform: translateX(-100%) skewX(-12deg);
          }
          100% {
            transform: translateX(200%) skewX(-12deg);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out forwards;
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
};

export default ItemCards;