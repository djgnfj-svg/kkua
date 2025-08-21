import React from 'react';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  helperText?: string;
  variant?: 'default' | 'glass' | 'filled';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  variant = 'default',
  size = 'md',
  icon,
  className = '',
  ...props
}) => {
  const baseClasses = 'w-full border rounded-xl focus:outline-none focus:ring-2 focus:ring-offset-0 transition-all duration-300 placeholder-secondary-400 font-korean';
  
  const variantClasses = {
    default: 'bg-white/10 backdrop-blur-sm border-white/30 focus:border-purple-500 focus:ring-purple-500/20 hover:border-white/50 text-white placeholder-white/50',
    glass: 'bg-white/10 backdrop-blur-sm border-white/30 focus:border-purple-500 focus:ring-purple-500/20 hover:bg-white/20 text-white placeholder-white/50',
    filled: 'bg-white/10 backdrop-blur-sm border-white/20 focus:bg-white/20 focus:border-purple-500 focus:ring-purple-500/20 hover:bg-white/15 text-white placeholder-white/50'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-5 py-4 text-lg'
  };
  
  const errorClasses = error
    ? 'border-danger-300 focus:border-danger-500 focus:ring-danger-200 bg-danger-50/50'
    : '';

  const inputClasses = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    errorClasses,
    icon ? 'pl-10' : '',
    className
  ].join(' ');

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-semibold text-white mb-2 font-korean">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400">
            {icon}
          </div>
        )}
        <input
          className={inputClasses}
          {...props}
        />
      </div>
      {(error || helperText) && (
        <p className={`mt-2 text-sm font-korean ${error ? 'text-red-400' : 'text-white/60'}`}>
          {error || helperText}
        </p>
      )}
    </div>
  );
};

export default Input;