import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'elevated' | 'gradient';
  hover?: boolean;
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> & {
  Header: React.FC<CardHeaderProps>;
  Body: React.FC<CardBodyProps>;
  Footer: React.FC<CardFooterProps>;
} = ({ 
  children, 
  className = '', 
  variant = 'default',
  hover = false 
}) => {
  const baseClasses = 'rounded-2xl transition-all duration-300 ease-out';
  
  const variantClasses = {
    default: 'bg-white/10 backdrop-blur-md shadow-xl border border-white/20 hover:shadow-2xl',
    glass: 'bg-white/10 backdrop-blur-md shadow-glass border border-white/20 hover:bg-white/20',
    elevated: 'bg-white/10 backdrop-blur-md shadow-2xl border border-white/20 hover:shadow-3xl transform hover:-translate-y-1',
    gradient: 'bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-md shadow-lg border border-white/20 hover:shadow-xl'
  };
  
  const hoverClasses = hover ? 'hover:scale-[1.02] cursor-pointer' : '';
  
  const classes = [
    baseClasses,
    variantClasses[variant],
    hoverClasses,
    className
  ].join(' ');

  return (
    <div className={classes}>
      {children}
    </div>
  );
};

const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '' }) => {
  const baseClasses = 'px-6 py-5 border-b border-white/20 bg-gradient-to-r from-purple-500/10 to-pink-500/10';
  const classes = [baseClasses, className].join(' ');

  return (
    <div className={classes}>
      {children}
    </div>
  );
};

const CardBody: React.FC<CardBodyProps> = ({ children, className = '' }) => {
  const baseClasses = 'px-6 py-5';
  const classes = [baseClasses, className].join(' ');

  return (
    <div className={classes}>
      {children}
    </div>
  );
};

const CardFooter: React.FC<CardFooterProps> = ({ children, className = '' }) => {
  const baseClasses = 'px-6 py-5 border-t border-white/20 bg-white/5 rounded-b-2xl';
  const classes = [baseClasses, className].join(' ');

  return (
    <div className={classes}>
      {children}
    </div>
  );
};

Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;

export default Card;