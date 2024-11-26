import React from 'react';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  prefix?: React.ReactNode;
  className?: string;
}

export const Input: React.FC<InputProps> = ({ 
  prefix, 
  className = '', 
  ...props 
}) => {
  return (
    <div className="relative">
      {prefix && (
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {prefix}
        </div>
      )}
      <input
        className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${prefix ? 'pl-10' : ''} ${className}`}
        {...props}
      />
    </div>
  );
};
