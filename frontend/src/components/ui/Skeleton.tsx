import React from 'react';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  width = '100%',
  height = '1rem',
  rounded = false
}) => {
  const widthStyle = typeof width === 'number' ? `${width}px` : width;
  const heightStyle = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={`animate-pulse bg-gray-200 ${rounded ? 'rounded-full' : 'rounded'} ${className}`}
      style={{
        width: widthStyle,
        height: heightStyle
      }}
    />
  );
};

export const PlayerListSkeleton: React.FC = () => (
  <div className="space-y-3">
    {[1, 2, 3, 4].map((i) => (
      <div key={i} className="flex items-center space-x-3 p-3 rounded-lg border">
        <Skeleton width={40} height={40} rounded />
        <div className="flex-1 space-y-2">
          <Skeleton width="60%" height={16} />
          <Skeleton width="40%" height={12} />
        </div>
        <Skeleton width={60} height={24} />
      </div>
    ))}
  </div>
);

export const GameBoardSkeleton: React.FC = () => (
  <div className="space-y-4">
    <div className="p-4 border rounded-lg">
      <Skeleton height={20} className="mb-4" />
      <div className="grid grid-cols-4 gap-2">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <Skeleton key={i} height={30} />
        ))}
      </div>
    </div>
    <div className="flex space-x-4">
      <Skeleton width="70%" height={40} />
      <Skeleton width="30%" height={40} />
    </div>
  </div>
);

export const ChatSkeleton: React.FC = () => (
  <div className="space-y-3">
    {[1, 2, 3].map((i) => (
      <div key={i} className={`p-2 rounded ${i % 2 === 0 ? 'ml-8' : 'mr-8'}`}>
        <div className="flex items-center justify-between mb-1">
          <Skeleton width="30%" height={12} />
          <Skeleton width={50} height={10} />
        </div>
        <Skeleton width="80%" height={14} />
      </div>
    ))}
  </div>
);

export default Skeleton;