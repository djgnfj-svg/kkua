import React, { useState, useEffect } from 'react';

interface DistractionEffectsProps {
  effects: DistractionEffect[];
  className?: string;
}

interface DistractionEffect {
  id: string;
  type: 'cat_distraction' | 'screen_shake' | 'blur_screen' | 'falling_objects' | 'color_invert';
  duration: number;
  value?: any;
}

interface CatProps {
  id: number;
  startDelay: number;
}

const Cat: React.FC<CatProps> = ({ id, startDelay }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: -100, y: 50 });
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
      const startY = Math.random() * 60 + 20; // 20-80% 위치
      setPosition({ x: -100, y: startY });
      
      // 애니메이션 시작
      setTimeout(() => {
        setPosition({ x: window.innerWidth + 100, y: startY });
      }, 50);
      
      // 애니메이션 완료 후 제거
      setTimeout(() => {
        setIsVisible(false);
      }, 4000); // 4초 후 제거
    }, startDelay);
    
    return () => clearTimeout(timer);
  }, [startDelay]);

  const catEmojis = ['😸', '🐱', '😹', '😺', '😻', '🙀'];
  const randomCat = catEmojis[id % catEmojis.length];

  if (!isVisible) return null;

  return (
    <div
      className="fixed pointer-events-none z-50 text-4xl select-none transition-all duration-[4000ms] linear cat-run"
      style={{
        left: `${position.x}px`,
        top: `${position.y}vh`,
        transform: 'translateX(0)',
      }}
    >
      {randomCat}
    </div>
  );
};

interface FallingObjectProps {
  type: string;
  id: number;
  startDelay: number;
}

const FallingObject: React.FC<FallingObjectProps> = ({ type, id, startDelay }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 50, y: -50, rotate: 0 });
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
      const startX = Math.random() * 90 + 5; // 5-95% 위치
      const swayAmount = (Math.random() - 0.5) * 50; // -25px ~ 25px 좌우 흔들림
      const rotation = Math.random() * 360;
      
      setPosition({ x: startX, y: -50, rotate: 0 });
      
      // 애니메이션 시작
      setTimeout(() => {
        setPosition({ 
          x: startX + swayAmount, 
          y: window.innerHeight + 50, 
          rotate: rotation 
        });
      }, 50);
      
      // 애니메이션 완료 후 제거
      setTimeout(() => {
        setIsVisible(false);
      }, 6000); // 6초 후 제거
    }, startDelay);
    
    return () => clearTimeout(timer);
  }, [startDelay]);

  const objectEmojis = {
    leaves: ['🍃', '🍂', '🌿'],
    hearts: ['💕', '💖', '💝', '💗'],
    stars: ['⭐', '✨', '🌟', '💫'],
    snow: ['❄️', '☃️', '🌨️']
  };
  
  const emojis = objectEmojis[type as keyof typeof objectEmojis] || objectEmojis.leaves;
  const randomEmoji = emojis[id % emojis.length];

  if (!isVisible) return null;

  return (
    <div
      className="fixed pointer-events-none z-40 text-2xl select-none transition-all duration-[6000ms] ease-in"
      style={{
        left: `${position.x}vw`,
        top: `${position.y}px`,
        transform: `rotate(${position.rotate}deg)`,
      }}
    >
      {randomEmoji}
    </div>
  );
};

export const DistractionEffects: React.FC<DistractionEffectsProps> = ({ 
  effects, 
  className = "" 
}) => {
  const [cats, setCats] = useState<number[]>([]);
  const [fallingObjects, setFallingObjects] = useState<{type: string, objects: number[]}[]>([]);
  const [screenEffects, setScreenEffects] = useState<{
    shake: boolean;
    blur: boolean;
    invert: boolean;
  }>({
    shake: false,
    blur: false,
    invert: false
  });

  useEffect(() => {
    effects.forEach(effect => {
      switch (effect.type) {
        case 'cat_distraction':
          const catCount = effect.value?.cat_count || 3;
          const newCats = Array.from({ length: catCount }, (_, i) => i);
          setCats(prev => [...prev, ...newCats]);
          
          // 지속 시간 후 제거
          setTimeout(() => {
            setCats(prev => prev.slice(catCount));
          }, effect.duration * 1000);
          break;
          
        case 'screen_shake':
          setScreenEffects(prev => ({ ...prev, shake: true }));
          setTimeout(() => {
            setScreenEffects(prev => ({ ...prev, shake: false }));
          }, effect.duration * 1000);
          break;
          
        case 'blur_screen':
          setScreenEffects(prev => ({ ...prev, blur: true }));
          setTimeout(() => {
            setScreenEffects(prev => ({ ...prev, blur: false }));
          }, effect.duration * 1000);
          break;
          
        case 'color_invert':
          setScreenEffects(prev => ({ ...prev, invert: true }));
          setTimeout(() => {
            setScreenEffects(prev => ({ ...prev, invert: false }));
          }, effect.duration * 1000);
          break;
          
        case 'falling_objects':
          const objectType = effect.value?.object_type || 'leaves';
          const objectCount = 15 + Math.random() * 10; // 15-25개 오브젝트
          const newObjects = Array.from({ length: objectCount }, (_, i) => i);
          
          setFallingObjects(prev => [...prev, { type: objectType, objects: newObjects }]);
          
          // 지속 시간 후 제거
          setTimeout(() => {
            setFallingObjects(prev => 
              prev.filter(item => item.type !== objectType || item.objects !== newObjects)
            );
          }, effect.duration * 1000 + 2000); // 애니메이션 완료 여유시간
          break;
      }
    });
  }, [effects]);

  // 화면 전체 효과를 위한 클래스 생성
  const getScreenEffectClasses = () => {
    let classes = className;
    
    if (screenEffects.shake) {
      classes += ' animate-shake';
    }
    if (screenEffects.blur) {
      classes += ' backdrop-blur-sm';
    }
    if (screenEffects.invert) {
      classes += ' invert';
    }
    
    return classes;
  };

  return (
    <>
      {/* 화면 효과 래퍼 */}
      <div className={getScreenEffectClasses()}>
        {/* 고양이 효과 */}
        {cats.map((catId, index) => (
          <Cat 
            key={`cat-${catId}-${Date.now()}-${index}`} 
            id={catId}
            startDelay={index * 500} // 0.5초 간격으로 출현
          />
        ))}
        
        {/* 떨어지는 오브젝트 효과 */}
        {fallingObjects.map((group, groupIndex) => 
          group.objects.map((objId, index) => (
            <FallingObject
              key={`${group.type}-${objId}-${Date.now()}-${groupIndex}-${index}`}
              type={group.type}
              id={objId}
              startDelay={index * 200} // 0.2초 간격으로 떨어짐
            />
          ))
        )}
      </div>

      {/* 흐림 효과를 위한 오버레이 */}
      {screenEffects.blur && (
        <div 
          className="fixed inset-0 pointer-events-none z-30 backdrop-blur-[2px] bg-white/10"
          style={{ backdropFilter: 'blur(2px)' }}
        />
      )}
    </>
  );
};

export default DistractionEffects;