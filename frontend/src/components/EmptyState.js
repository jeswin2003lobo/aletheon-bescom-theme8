import React from 'react';
import { Inbox } from 'lucide-react';

export function EmptyState({ message, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <Inbox className="w-5 h-5 text-[#808080] mb-3" />
      <p className="text-sm text-[#808080]">
        {message || 'No data available'}
      </p>
    </div>
  );
}
