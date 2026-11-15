import React from 'react';
import { getScoreColorClass } from '../../utils/formatters';

interface ScoreBarProps {
  score: number;
  showText?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({
  score,
  showText = true,
  size = 'md',
  className = '',
}) => {
  const clampedScore = Math.max(0, Math.min(100, score));
  const colors = getScoreColorClass(clampedScore);

  const heightStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-3.5',
  };

  return (
    <div className={`w-full flex items-center gap-3 ${className}`}>
      <div className={`flex-1 bg-slate-100 rounded-full overflow-hidden ${heightStyles[size]}`}>
        <div
          className={`${heightStyles[size]} rounded-full transition-all duration-500 ${colors.progress}`}
          style={{ width: `${clampedScore}%` }}
        />
      </div>
      {showText && (
        <span className={`text-xs font-semibold font-mono w-12 text-right ${colors.text}`}>
          {clampedScore.toFixed(1)}%
        </span>
      )}
    </div>
  );
};
