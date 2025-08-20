import React from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  overlay?: boolean;
  variant?: 'spinner' | 'dots' | 'pulse';
}

const Loading: React.FC<LoadingProps> = ({ 
  size = 'md', 
  text,
  overlay = false,
  variant = 'spinner'
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const dotSize = {
    sm: 'w-1 h-1',
    md: 'w-2 h-2',
    lg: 'w-3 h-3',
    xl: 'w-4 h-4'
  };

  const renderSpinner = () => (
    <div className="animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
  );

  const renderDots = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`${dotSize[size]} bg-primary-600 rounded-full animate-bounce`}
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );

  const renderPulse = () => (
    <div className={`${sizeClasses[size]} bg-primary-600 rounded-full animate-pulse`} />
  );

  const getLoader = () => {
    switch (variant) {
      case 'dots':
        return renderDots();
      case 'pulse':
        return renderPulse();
      default:
        return <div className={sizeClasses[size]}>{renderSpinner()}</div>;
    }
  };

  const content = (
    <div className="flex flex-col items-center justify-center space-y-4 animate-fade-in">
      {getLoader()}
      {text && (
        <p className="text-sm text-secondary-600 font-korean animate-pulse">
          {text}
        </p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-secondary-900/20 backdrop-blur-sm">
        <div className="bg-white/95 backdrop-blur-md rounded-2xl p-8 shadow-glass border border-white/30">
          {content}
        </div>
      </div>
    );
  }

  return content;
};

export default Loading;