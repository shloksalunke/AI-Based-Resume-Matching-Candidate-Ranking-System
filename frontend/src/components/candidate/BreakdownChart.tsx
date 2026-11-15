import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import type { ScoreBreakdown } from '../../types';

interface BreakdownChartProps {
  breakdown: ScoreBreakdown;
}

export const BreakdownChart: React.FC<BreakdownChartProps> = ({ breakdown }) => {
  const data = [
    {
      category: 'Skills (40%)',
      earned: breakdown.skills?.score || 0,
      max: breakdown.skills?.max || 40,
    },
    {
      category: 'Semantic (25%)',
      earned: breakdown.semantic?.score || 0,
      max: breakdown.semantic?.max || 25,
    },
    {
      category: 'Experience (20%)',
      earned: breakdown.experience?.score || 0,
      max: breakdown.experience?.max || 20,
    },
    {
      category: 'Education (10%)',
      earned: breakdown.education?.score || 0,
      max: breakdown.education?.max || 10,
    },
    {
      category: 'Relevance (5%)',
      earned: breakdown.relevance?.score || 0,
      max: breakdown.relevance?.max || 5,
    },
  ];

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis dataKey="category" tick={{ fill: '#64748b', fontSize: 12 }} />
          <YAxis tick={{ fill: '#64748b', fontSize: 12 }} domain={[0, 40]} />
          <Tooltip
            formatter={(value: unknown, name: unknown) => [
              `${Number(value).toFixed(1)} pts`,
              name === 'earned' ? 'Candidate Score' : 'Maximum Weight',
            ]}
            contentStyle={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
          />
          <Legend />
          <Bar dataKey="earned" name="Candidate Score" fill="#4f46e5" radius={[4, 4, 0, 0]} />
          <Bar dataKey="max" name="Maximum Points" fill="#cbd5e1" radius={[4, 4, 0, 0]} opacity={0.6} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
