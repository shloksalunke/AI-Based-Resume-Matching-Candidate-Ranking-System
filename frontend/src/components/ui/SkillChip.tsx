import React from 'react';

export type SkillChipStatus = 'matched' | 'partial' | 'missing' | 'default';

interface SkillChipProps {
  name: string;
  status?: SkillChipStatus;
  size?: 'sm' | 'md';
  className?: string;
}

export const SkillChip: React.FC<SkillChipProps> = ({
  name,
  status = 'default',
  size = 'md',
  className = '',
}) => {
  const statusStyles = {
    matched: 'bg-emerald-50 text-emerald-800 border-emerald-200/90 hover:bg-emerald-100',
    partial: 'bg-amber-50 text-amber-800 border-amber-200/90 hover:bg-amber-100',
    missing: 'bg-rose-50 text-rose-700 border-rose-200/90 hover:bg-rose-100',
    default: 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border font-medium transition-colors ${statusStyles[status]} ${sizeStyles[size]} ${className}`}
    >
      {status === 'matched' && <span className="mr-1 text-emerald-600 font-bold">✓</span>}
      {status === 'partial' && <span className="mr-1 text-amber-600 font-bold">~</span>}
      {status === 'missing' && <span className="mr-1 text-rose-500 font-bold">✕</span>}
      {name}
    </span>
  );
};
