import React, { useState, useEffect, useCallback } from 'react';
import { Button, Card } from './ui';
import { apiEndpoints } from '../utils/api';
import { showToast } from './Toast';

interface ItemInfo {
  id: number;
  name: string;
  description: string;
  rarity: string;
  effect_type: string;
  effect_value: any;
  cooldown_seconds: number;
}

interface InventoryItem extends ItemInfo {
  quantity: number;
  cooldown_remaining?: number;
}

interface ItemPanelProps {
  userId: number;
  roomId?: string;
  isGameActive: boolean;
  isMyTurn: boolean;
  onItemUse?: (itemId: number, targetUserId?: number) => void;
}

const rarityColors = {
  common: 'bg-gray-100 border-gray-300 text-gray-800',
  uncommon: 'bg-green-100 border-green-300 text-green-800', 
  rare: 'bg-blue-100 border-blue-300 text-blue-800',
  epic: 'bg-purple-100 border-purple-300 text-purple-800',
  legendary: 'bg-yellow-100 border-yellow-300 text-yellow-800'
};

const rarityIcons = {
  common: '⚪',
  uncommon: '🟢',
  rare: '🔵', 
  epic: '🟣',
  legendary: '🟡'
};

export const ItemPanel: React.FC<ItemPanelProps> = ({
  userId,
  // roomId, // 사용하지 않음
  isGameActive,
  isMyTurn,
  onItemUse
}) => {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  // const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null); // 나중에 사용 예정

  const loadInventory = useCallback(async () => {
    if (!userId) return;

    try {
      setLoading(true);
      const response = await apiEndpoints.items.inventory(userId);
      
      if (response.data.success) {
        setInventory(response.data.inventory || []);
      }
    } catch (error) {
      console.error('인벤토리 로딩 실패:', error);
      showToast.error('인벤토리를 불러올 수 없습니다');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  const handleItemUse = useCallback((item: InventoryItem) => {
    if (!isGameActive) {
      showToast.warning('게임이 진행 중일 때만 아이템을 사용할 수 있습니다');
      return;
    }

    if (!isMyTurn && item.effect_type !== 'freeze_opponent') {
      showToast.warning('내 턴일 때만 이 아이템을 사용할 수 있습니다');
      return;
    }

    if (item.cooldown_remaining && item.cooldown_remaining > 0) {
      showToast.warning(`아이템 쿨다운 중입니다 (${item.cooldown_remaining}초 남음)`);
      return;
    }

    if (item.quantity <= 0) {
      showToast.warning('보유한 아이템이 없습니다');
      return;
    }

    // 타겟이 필요한 아이템인지 확인
    const needsTarget = ['freeze_opponent', 'steal_word'].includes(item.effect_type);
    
    if (needsTarget) {
      // 임시 구현: 랜덤 상대방 선택 (실제로는 타겟 선택 모달 필요)
      const targetUserId = Math.floor(Math.random() * 1000) + 1;
      onItemUse?.(item.id, targetUserId);
      showToast.success(`${item.name} 사용! (랜덤 타겟)`);
    } else {
      // 즉시 사용
      onItemUse?.(item.id);
      showToast.success(`${item.name} 사용!`);
      
      // 로컬 상태 업데이트 (낙관적 업데이트)
      setInventory(prev => prev.map(invItem => 
        invItem.id === item.id 
          ? { ...invItem, quantity: invItem.quantity - 1, cooldown_remaining: item.cooldown_seconds }
          : invItem
      ));
    }
  }, [isGameActive, isMyTurn, onItemUse]);

  const getItemEffectDescription = (item: InventoryItem): string => {
    switch (item.effect_type) {
      case 'time_extend':
        return `⏰ 시간 ${item.effect_value?.seconds || 10}초 연장`;
      case 'score_multiplier':
        return `⚡ 다음 단어 점수 ${item.effect_value?.multiplier || 2}배`;
      case 'word_hint':
        return `💡 다음 글자 힌트 ${item.effect_value?.hint_count || 3}개`;
      case 'freeze_opponent':
        return `❄️ 상대방 시간 ${item.effect_value?.seconds || 5}초 단축`;
      case 'shield':
        return `🛡️ 한 턴 동안 공격 무효화`;
      case 'combo_boost':
        return `🔥 콤보 ${item.effect_value?.boost || 3} 추가`;
      case 'extra_turn':
        return `🔄 추가 턴 획득`;
      case 'steal_word':
        return `🎯 상대방 단어 1개 무효화`;
      case 'revive':
        return `💖 한 번 더 기회`;
      default:
        return item.description;
    }
  };

  return (
    <Card>
      <Card.Header>
        <div className="flex items-center justify-between">
          <h3 className="text-base sm:text-lg font-semibold">🎒 아이템</h3>
          <Button
            variant="secondary"
            size="sm"
            onClick={loadInventory}
            disabled={loading}
          >
            {loading ? '⟳' : '🔄'}
          </Button>
        </div>
      </Card.Header>
      
      <Card.Body>
        {loading ? (
          <div className="text-center py-4 text-gray-500">
            아이템 로딩 중...
          </div>
        ) : inventory.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            보유한 아이템이 없습니다
          </div>
        ) : (
          <div className="space-y-2 max-h-56 sm:max-h-64 overflow-y-auto">
            {inventory.map((item) => (
              <div
                key={item.id}
                className={`border rounded-lg p-2 sm:p-3 ${rarityColors[item.rarity as keyof typeof rarityColors] || 'bg-gray-50'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span>{rarityIcons[item.rarity as keyof typeof rarityIcons] || '⚫'}</span>
                    <span className="font-semibold text-xs sm:text-sm truncate">{item.name}</span>
                    <span className="text-xs bg-white bg-opacity-50 px-1 sm:px-2 py-1 rounded-full flex-shrink-0">
                      x{item.quantity}
                    </span>
                  </div>
                  
                  {item.quantity > 0 && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleItemUse(item)}
                      disabled={
                        !isGameActive || 
                        (item.cooldown_remaining && item.cooldown_remaining > 0) ||
                        (!isMyTurn && item.effect_type !== 'freeze_opponent')
                      }
                      className="px-2 py-1 text-xs"
                    >
                      {item.cooldown_remaining && item.cooldown_remaining > 0 
                        ? `${item.cooldown_remaining}s` 
                        : '사용'
                      }
                    </Button>
                  )}
                </div>
                
                <div className="text-xs opacity-80 mb-1">
                  {getItemEffectDescription(item)}
                </div>
                
                <div className="text-xs opacity-60">
                  쿨다운: {item.cooldown_seconds}초
                </div>
              </div>
            ))}
          </div>
        )}

        {!isGameActive && inventory.length > 0 && (
          <div className="mt-3 text-xs text-center text-gray-500 bg-yellow-50 p-2 rounded">
            💡 게임 중에만 아이템을 사용할 수 있습니다
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default ItemPanel;