import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'ghost' | 'glass';
type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  glow?: boolean;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  glow = false,
  disabled,
  className = '',
  children,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-300 ease-out focus:outline-none focus:ring-2 focus:ring-offset-2 transform hover:scale-[1.02] active:scale-[0.98] backdrop-blur-xs';
  
  const variantClasses = {
    primary: 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 focus:ring-purple-500 text-white shadow-lg hover:shadow-xl shadow-purple-500/25 border-0',
    secondary: 'bg-white/10 hover:bg-white/20 focus:ring-white/30 text-white border border-white/20 hover:border-white/30 shadow-sm hover:shadow-md backdrop-blur-md',
    success: 'bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 focus:ring-green-500 text-white shadow-lg hover:shadow-xl shadow-green-500/25 border-0',
    danger: 'bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-600 hover:to-rose-600 focus:ring-red-500 text-white shadow-lg hover:shadow-xl shadow-red-500/25 border-0',
    warning: 'bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 focus:ring-yellow-500 text-white shadow-lg hover:shadow-xl shadow-yellow-500/25 border-0',
    ghost: 'bg-transparent hover:bg-white/10 focus:ring-white/30 text-white border border-transparent hover:border-white/20',
    glass: 'bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/20 focus:ring-white/30 text-white shadow-glass hover:shadow-glow-sm'
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm h-8',
    md: 'px-5 py-2.5 text-base h-10',
    lg: 'px-6 py-3 text-lg h-12',
    xl: 'px-8 py-4 text-xl h-14'
  };

  const glowClasses = glow ? 'animate-glow' : '';
  const loadingClasses = loading ? 'cursor-wait' : '';
  const disabledClasses = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:hover:scale-100 disabled:hover:shadow-none disabled:animate-none';

  const classes = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    glowClasses,
    loadingClasses,
    disabledClasses,
    className
  ].join(' ');

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <div className="inline-flex items-center mr-2">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent opacity-70"></div>
        </div>
      )}
      {children}
    </button>
  );
};

export default Button;