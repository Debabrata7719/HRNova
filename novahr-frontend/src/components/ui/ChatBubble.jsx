import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import botAvatar from '../../assets/bot-avatar.png';

const ChatBubble = ({ message, isBot = false, timestamp, userInitial = 'U' }) => {
  return (
    <motion.div
      className={clsx('flex gap-3 mb-4', isBot ? 'justify-start' : 'justify-end')}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {isBot && (
        <div className="flex-shrink-0 w-9 h-9 rounded-full overflow-hidden bg-white">
          <img src={botAvatar} alt="NovaHR Bot" className="w-full h-full object-contain" />
        </div>
      )}

      <div className={clsx(
        'max-w-[70%] rounded-2xl px-4 py-3',
        isBot
          ? 'bg-zinc-800 border border-zinc-700 text-white rounded-tl-none'
          : 'bg-blue-600 text-white rounded-tr-none'
      )}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        {timestamp && (
          <p className={clsx('text-xs mt-1', isBot ? 'text-zinc-400' : 'text-blue-100')}>
            {timestamp}
          </p>
        )}
      </div>

      {!isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
          {userInitial}
        </div>
      )}
    </motion.div>
  );
};

export default ChatBubble;
