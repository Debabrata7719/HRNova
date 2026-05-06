import React from 'react';
import clsx from 'clsx';

const Card = ({ 
  children, 
  className = '',
  hover = false,
  ...props 
}) => {
  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-md p-6 border border-gray-200',
        hover && 'hover:shadow-lg hover:scale-105 transition-all duration-200 cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
