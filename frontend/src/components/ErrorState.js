import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export function ErrorState({ message, onRetry, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <AlertCircle className="w-5 h-5 text-[#808080] mb-3" />
      <p className="text-sm text-[#999999] mb-3 text-center max-w-md">
        {message || 'Unable to load data'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1.5 text-xs text-[#999999] hover:text-[#FAFAFA] transition-colors duration-200"
          data-testid="retry-button"
        >
          <RefreshCw className="w-3 h-3" />
          Retry
        </button>
      )}
    </div>
  );
}

export function InlineError({ message }) {
  return (
    <p className="text-xs text-[#EF4444]/80 mt-1">{message}</p>
  );
}
