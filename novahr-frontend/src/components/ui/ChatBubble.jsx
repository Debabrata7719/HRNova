import React from 'react';
import clsx from 'clsx';

const ChatBubble = ({ message, isBot = false, timestamp, userInitial = 'U' }) => {
  return (
    <div className={clsx(
      'flex gap-3 mb-4 animate-fade-in',
      isBot ? 'justify-start' : 'justify-end'
    )}>
      {isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
          🤖
        </div>
      )}
      
      <div className={clsx(
        'max-w-[70%] rounded-2xl px-4 py-3 shadow-sm',
        isBot 
          ? 'bg-gray-100 text-gray-900 rounded-tl-none' 
          : 'bg-blue-600 text-white rounded-tr-none'
      )}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        {timestamp && (
          <p className={clsx(
            'text-xs mt-1',
            isBot ? 'text-gray-500' : 'text-blue-100'
          )}>
            {timestamp}
          </p>
        )}
      </div>
      
      {!isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
          {userInitial}
        </div>
      )}
    </div>
  );
};

export default ChatBubble;
