import React from 'react';
import { getScoreColorClass } from '../../utils/formatters';

interface ScoreGaugeProps {
  score: number;
  size?: number;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({ score, size = 140 }) => {
  const clamped = Math.max(0, Math.min(100, score));
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (clamped / 100) * circumference;
  const color = getScoreColorClass(clamped);

  let label = 'Low Match';
  if (clamped >= 75) label = 'Strong Fit';
  else if (clamped >= 50) label = 'Moderate Fit';

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#f1f5f9"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={clamped >= 75 ? '#10b981' : clamped >= 50 ? '#f59e0b' : '#f43f5e'}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-extrabold font-mono tracking-tight text-slate-900">
            {clamped.toFixed(1)}
            <span className="text-base font-normal text-slate-500">%</span>
          </span>
          <span className={`text-[11px] font-semibold uppercase tracking-wider mt-0.5 ${color.text}`}>
            {label}
          </span>
        </div>
      </div>
    </div>
  );
};
