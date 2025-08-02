import React, { useState, useEffect } from 'react';
import { itemApi } from '../../../Api/itemApi';

const ItemPanel = ({ roomId, onItemUsed, isMyTurn, canUseItems = true }) => {
  const [inventory, setInventory] = useState([]);
  const [activeEffects, setActiveEffects] = useState([]);
  const [cooldowns, setCooldowns] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  // 아이템 상태 조회
  const fetchItemState = async () => {
    try {
      setLoading(true);
      const itemState = await itemApi.getGameItemState(roomId);
      setInventory(itemState.available_items || []);
      setActiveEffects(itemState.active_effects || []);
      setCooldowns(itemState.cooldowns || {});
    } catch (error) {
      console.error('아이템 상태 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItemState();
    // 주기적으로 아이템 상태 업데이트
    const interval = setInterval(fetchItemState, 5000);
    return () => clearInterval(interval);
  }, [roomId]);

  // 아이템 사용
  const handleItemUse = async (item) => {
    try {
      const result = await itemApi.useItemInGame(roomId, item.item.item_id);
      
      if (result.success) {
        // 성공 시 상태 업데이트
        await fetchItemState();
        onItemUsed?.(item, result);
        
        // 성공 메시지 표시
        showMessage(result.message, 'success');
      } else {
        // 실패 메시지 표시
        showMessage(result.message, 'error');
      }
    } catch (error) {
      console.error('아이템 사용 실패:', error);
      showMessage('아이템 사용 중 오류가 발생했습니다', 'error');
    }
  };

  // 메시지 표시 (토스트 등)
  const showMessage = (message, type) => {
    // 추후 토스트 컨텍스트 연결
    console.log(`[${type}] ${message}`);
  };

  // 아이템 사용 가능 여부 확인
  const canUseItem = (item) => {
    if (!canUseItems || !isMyTurn) return false;
    if (item.quantity <= 0) return false;
    if (cooldowns[item.item.item_id] > 0) return false;
    return true;
  };

  // 아이템 아이콘 매핑
  const getItemIcon = (effectType) => {
    const iconMap = {
      skip_turn: '⏭️',
      extra_time: '⏰',
      score_multiplier: '⭐',
      word_hint: '💡',
      immunity: '🛡️'
    };
    return iconMap[effectType] || '📦';
  };

  // 희귀도별 색상
  const getRarityColor = (rarity) => {
    const colorMap = {
      common: 'border-gray-300 bg-gray-50',
      rare: 'border-blue-300 bg-blue-50',
      epic: 'border-purple-300 bg-purple-50',
      legendary: 'border-orange-300 bg-orange-50'
    };
    return colorMap[rarity] || 'border-gray-300 bg-gray-50';
  };

  if (loading && inventory.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded mb-2"></div>
          <div className="grid grid-cols-3 gap-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-800 flex items-center">
          🎒 아이템
        </h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {showDetails ? '간단히' : '자세히'}
        </button>
      </div>

      {/* 활성 효과 표시 */}
      {activeEffects.length > 0 && (
        <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded">
          <div className="text-sm font-medium text-green-800 mb-1">활성 효과</div>
          {activeEffects.map((effect, index) => (
            <div key={index} className="text-xs text-green-700">
              {getItemIcon(effect.effect_type)} {effect.source_item}
            </div>
          ))}
        </div>
      )}

      {/* 아이템 목록 */}
      {inventory.length === 0 ? (
        <div className="text-center py-4 text-gray-500">
          <div className="text-2xl mb-2">📦</div>
          <div className="text-sm">보유 중인 아이템이 없습니다</div>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {inventory.map((inventoryItem) => {
            const item = inventoryItem.item;
            const isUsable = canUseItem(inventoryItem);
            const remainingCooldown = cooldowns[item.item_id] || 0;

            return (
              <div
                key={inventoryItem.inventory_id}
                className={`
                  relative border-2 rounded-lg p-2 cursor-pointer transition-all duration-200
                  ${getRarityColor(item.rarity)}
                  ${isUsable 
                    ? 'hover:scale-105 hover:shadow-md' 
                    : 'opacity-50 cursor-not-allowed'
                  }
                  ${selectedItem?.inventory_id === inventoryItem.inventory_id 
                    ? 'ring-2 ring-blue-400' 
                    : ''
                  }
                `}
                onClick={() => {
                  if (isUsable) {
                    setSelectedItem(inventoryItem);
                    handleItemUse(inventoryItem);
                  }
                }}
              >
                {/* 아이템 아이콘 */}
                <div className="text-center">
                  <div className="text-2xl mb-1">
                    {getItemIcon(item.effect_type)}
                  </div>
                  
                  {/* 아이템 이름 */}
                  <div className="text-xs font-medium text-gray-800 truncate">
                    {item.name}
                  </div>
                  
                  {/* 수량 */}
                  <div className="text-xs text-gray-600">
                    ×{inventoryItem.quantity}
                  </div>

                  {/* 쿨다운 표시 */}
                  {remainingCooldown > 0 && (
                    <div className="absolute inset-0 bg-gray-900 bg-opacity-50 rounded-lg flex items-center justify-center">
                      <div className="text-white text-xs font-bold">
                        {remainingCooldown}s
                      </div>
                    </div>
                  )}

                  {/* 상세 정보 (토글 시) */}
                  {showDetails && (
                    <div className="mt-1 text-xs text-gray-600">
                      <div>비용: {item.cost}</div>
                      <div>쿨다운: {item.cooldown_seconds}s</div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 사용 불가 상태 메시지 */}
      {!canUseItems && (
        <div className="mt-2 text-xs text-gray-500 text-center">
          {!isMyTurn ? '내 턴이 아닙니다' : '아이템을 사용할 수 없습니다'}
        </div>
      )}

      {/* 아이템 설명 툴팁 */}
      {selectedItem && showDetails && (
        <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
          <div className="font-medium">{selectedItem.item.name}</div>
          <div className="text-gray-600 mt-1">{selectedItem.item.description}</div>
        </div>
      )}
    </div>
  );
};

export default ItemPanel;