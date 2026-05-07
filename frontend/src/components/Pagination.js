import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function Pagination({ page, pageSize, totalRecords, onPageChange }) {
  if (!totalRecords) return null;
  
  const totalPages = Math.ceil(totalRecords / pageSize);
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalRecords);

  return (
    <div className="flex items-center justify-between py-3 text-xs text-[#999999]">
      <span>
        Showing {start}{'–'}{end} of {totalRecords}
      </span>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="p-1 hover:text-[#FAFAFA] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          data-testid="pagination-prev"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="font-mono">{page} / {totalPages}</span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="p-1 hover:text-[#FAFAFA] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          data-testid="pagination-next"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
