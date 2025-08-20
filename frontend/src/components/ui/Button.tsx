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
    primary: 'bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 focus:ring-primary-500 text-white shadow-lg hover:shadow-xl border-0',
    secondary: 'bg-secondary-100 hover:bg-secondary-200 focus:ring-secondary-400 text-secondary-700 border border-secondary-300 hover:border-secondary-400 shadow-sm hover:shadow-md',
    success: 'bg-gradient-to-r from-success-500 to-success-600 hover:from-success-600 hover:to-success-700 focus:ring-success-500 text-white shadow-lg hover:shadow-xl border-0',
    danger: 'bg-gradient-to-r from-danger-500 to-danger-600 hover:from-danger-600 hover:to-danger-700 focus:ring-danger-500 text-white shadow-lg hover:shadow-xl border-0',
    warning: 'bg-gradient-to-r from-warning-500 to-warning-600 hover:from-warning-600 hover:to-warning-700 focus:ring-warning-400 text-white shadow-lg hover:shadow-xl border-0',
    ghost: 'bg-transparent hover:bg-secondary-100 focus:ring-secondary-400 text-secondary-700 border border-transparent hover:border-secondary-300',
    glass: 'bg-glass-light backdrop-blur-md border border-white/20 hover:bg-glass-medium focus:ring-primary-500 text-secondary-800 shadow-glass hover:shadow-glow-sm'
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