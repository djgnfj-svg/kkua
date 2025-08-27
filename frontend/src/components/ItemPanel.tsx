import React, { useState, useEffect, useCallback } from 'react';
import { Button } from './ui';
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
  common: 'bg-gray-500/20 border-gray-400/30 text-gray-300',
  uncommon: 'bg-green-500/20 border-green-400/30 text-green-300', 
  rare: 'bg-blue-500/20 border-blue-400/30 text-blue-300',
  epic: 'bg-purple-500/20 border-purple-400/30 text-purple-300',
  legendary: 'bg-yellow-500/20 border-yellow-400/30 text-yellow-300'
};

const rarityIcons = {
  common: '⚪',
  uncommon: '🟢',
  rare: '🔵', 
  epic: '🟣',
  legendary: '🟡'
};

const getItemIcon = (effectType: string): string => {
  const iconMap = {
    // 기존 아이템들
    time_extend: '⏰',
    score_multiply: '💎',
    word_hint: '💡',
    time_attack: '⚡',
    shield: '🛡️',
    freeze: '❄️',
    double_turn: '🔄',
    word_steal: '🎯',
    combo_boost: '🚀',
    revival: '💖',
    
    // 새로운 방해 아이템들
    cat_distraction: '😸',
    screen_shake: '📳',
    blur_screen: '😵‍💫',
    falling_objects: '🍃',
    color_invert: '🎨'
  };
  
  return iconMap[effectType as keyof typeof iconMap] || '❓';
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
    const icon = getItemIcon(item.effect_type);
    
    switch (item.effect_type) {
      case 'time_extend':
        return `${icon} 시간 ${item.effect_value?.seconds || 10}초 연장`;
      case 'score_multiplier':
        return `${icon} 다음 단어 점수 ${item.effect_value?.multiplier || 2}배`;
      case 'word_hint':
        return `${icon} 다음 글자 힌트 ${item.effect_value?.hint_count || 3}개`;
      case 'freeze_opponent':
        return `${icon} 상대방 시간 ${item.effect_value?.seconds || 5}초 단축`;
      case 'shield':
        return `${icon} 한 턴 동안 공격 무효화`;
      case 'combo_boost':
        return `${icon} 콤보 ${item.effect_value?.boost || 3} 추가`;
      case 'extra_turn':
        return `${icon} 추가 턴 획득`;
      case 'steal_word':
        return `${icon} 상대방 단어 1개 무효화`;
      case 'revive':
        return `${icon} 한 번 더 기회`;
        
      // 새로운 방해 아이템들
      case 'cat_distraction':
        return `${icon} 고양이 ${item.effect_value?.cat_count || 3}마리가 ${item.effect_value?.duration || 5}초간 방해`;
      case 'screen_shake':
        return `${icon} 화면 흔들기 ${item.effect_value?.duration || 3}초`;
      case 'blur_screen':
        return `${icon} 화면 흐림 ${item.effect_value?.duration || 4}초`;
      case 'falling_objects':
        const objectType = item.effect_value?.object_type || 'leaves';
        const objectName = {
          leaves: '잎사귀',
          hearts: '하트',
          stars: '별',
          snow: '눈송이'
        }[objectType as keyof typeof objectName] || '오브젝트';
        return `${icon} ${objectName} 비 ${item.effect_value?.duration || 6}초`;
      case 'color_invert':
        return `${icon} 색상 반전 ${item.effect_value?.duration || 5}초`;
        
      default:
        return item.description || `${icon} 특별한 효과`;
    }
  };

  // 최대 5개 아이템만 표시
  const displayItems = inventory.slice(0, 5);
  
  // 빈 슬롯을 만들어 총 5개 슬롯 보장
  const slots = [...displayItems];
  while (slots.length < 5) {
    slots.push(null as any);
  }

  return (
    <div className="flex items-center space-x-2">
      {/* 아이템 슬롯들 */}
      <div className="flex space-x-1">
        {slots.map((item, index) => (
          <div
            key={index}
            className={`
              w-12 h-12 rounded-lg border-2 flex items-center justify-center
              transition-all duration-300 relative group cursor-pointer
              ${item 
                ? `${rarityColors[item.rarity as keyof typeof rarityColors] || 'bg-gray-500/20 border-gray-400/30'} hover:scale-110` 
                : 'bg-white/5 border-white/20 border-dashed'
              }
            `}
            onClick={() => item && handleItemUse(item)}
            title={item ? `${item.name} (${item.quantity}개)` : '빈 슬롯'}
          >
            {item ? (
              <>
                <span className="text-lg">{getItemIcon(item.effect_type)}</span>
                {/* 아이템 개수 표시 */}
                {item.quantity > 1 && (
                  <span className="absolute -top-1 -right-1 bg-purple-600 text-white text-xs w-4 h-4 rounded-full flex items-center justify-center font-bold">
                    {item.quantity > 9 ? '9+' : item.quantity}
                  </span>
                )}
                {/* 쿨다운 표시 */}
                {item.cooldown_remaining && item.cooldown_remaining > 0 && (
                  <span className="absolute -bottom-1 -right-1 bg-red-600 text-white text-xs px-1 rounded-full">
                    {item.cooldown_remaining}s
                  </span>
                )}
                {/* 호버 시 툴팁 */}
                <div className="absolute bottom-14 left-1/2 transform -translate-x-1/2 bg-black/90 text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                  <div className="font-bold">{item.name}</div>
                  <div className="text-gray-300">{getItemEffectDescription(item).replace(/[🎯⏰💎💡⚡🛡️❄️🔄🎯🚀💖😸📳😵‍💫🍃🎨❓]/g, '').trim()}</div>
                  {item.cooldown_remaining && item.cooldown_remaining > 0 ? (
                    <div className="text-red-300">쿨다운: {item.cooldown_remaining}초</div>
                  ) : !isGameActive ? (
                    <div className="text-yellow-300">게임 중에만 사용 가능</div>
                  ) : !isMyTurn && item.effect_type !== 'freeze_opponent' ? (
                    <div className="text-yellow-300">내 턴에만 사용 가능</div>
                  ) : (
                    <div className="text-green-300">클릭하여 사용</div>
                  )}
                </div>
              </>
            ) : (
              <span className="text-white/30">+</span>
            )}
          </div>
        ))}
      </div>
      
      {/* 새로고침 버튼 */}
      <button
        onClick={loadInventory}
        disabled={loading}
        className="w-8 h-8 rounded-lg bg-white/10 border border-white/20 flex items-center justify-center hover:bg-white/20 transition-colors"
        title="아이템 새로고침"
      >
        {loading ? (
          <span className="animate-spin text-sm">⟳</span>
        ) : (
          <span className="text-sm">🔄</span>
        )}
      </button>
    </div>
  );
};

export default ItemPanel;