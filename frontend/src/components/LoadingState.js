import React from 'react';

export function Skeleton({ className = '', variant = 'rect' }) {
  const baseClass = 'animate-pulse bg-[#222222] rounded-sm';
  
  if (variant === 'text') {
    return <div className={`${baseClass} h-4 ${className}`} />;
  }
  if (variant === 'title') {
    return <div className={`${baseClass} h-8 w-48 ${className}`} />;
  }
  if (variant === 'number') {
    return <div className={`${baseClass} h-10 w-24 ${className}`} />;
  }
  if (variant === 'card') {
    return (
      <div className={`${baseClass} p-6 border border-[#333333] ${className}`}>
        <div className="space-y-3">
          <div className="h-3 bg-[#252525] rounded w-1/3" />
          <div className="h-8 bg-[#252525] rounded w-1/2" />
        </div>
      </div>
    );
  }
  if (variant === 'table') {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className={`${baseClass} h-10 w-full`} style={{ animationDelay: `${i * 100}ms` }} />
        ))}
      </div>
    );
  }
  return <div className={`${baseClass} ${className}`} />;
}

export function KPISkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} variant="card" className="h-28" />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 8, cols = 5 }) {
  return (
    <div className="space-y-1">
      <div className="flex gap-4 py-3 border-b border-[#333333]">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} variant="text" className="flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 py-3 border-b border-[#333333]" style={{ animationDelay: `${i * 50}ms` }}>
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} variant="text" className="flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton({ height = 'h-64' }) {
  return (
    <div className={`animate-pulse bg-[#111111] border border-[#333333] rounded-sm ${height} flex items-end justify-center gap-2 p-6`}>
      {Array.from({ length: 12 }).map((_, i) => (
        <div
          key={i}
          className="bg-[#222222] rounded-sm flex-1"
          style={{ height: `${20 + Math.random() * 60}%`, animationDelay: `${i * 50}ms` }}
        />
      ))}
    </div>
  );
}
