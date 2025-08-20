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
    default: 'bg-white shadow-lg border border-secondary-200/50 hover:shadow-xl',
    glass: 'bg-white/80 backdrop-blur-md shadow-glass border border-white/30 hover:bg-white/90',
    elevated: 'bg-white shadow-2xl border-0 hover:shadow-3xl transform hover:-translate-y-1',
    gradient: 'bg-gradient-to-br from-white to-secondary-50 shadow-lg border border-secondary-200/30 hover:shadow-xl'
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
  const baseClasses = 'px-6 py-5 border-b border-secondary-200/60';
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
  const baseClasses = 'px-6 py-5 border-t border-secondary-200/60 bg-secondary-50/50 rounded-b-2xl';
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