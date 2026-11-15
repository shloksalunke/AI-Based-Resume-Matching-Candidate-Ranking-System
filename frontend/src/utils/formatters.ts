// Utility formatting functions for scores, dates and text labels

export const formatScore = (score: number): string => {
  return `${score.toFixed(1)}%`;
};

export const getScoreColorClass = (score: number): {
  bg: string;
  text: string;
  border: string;
  progress: string;
} => {
  if (score >= 75) {
    return {
      bg: 'bg-emerald-50',
      text: 'text-emerald-700',
      border: 'border-emerald-200',
      progress: 'bg-emerald-500',
    };
  }
  if (score >= 50) {
    return {
      bg: 'bg-amber-50',
      text: 'text-amber-700',
      border: 'border-amber-200',
      progress: 'bg-amber-500',
    };
  }
  return {
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    border: 'border-rose-200',
    progress: 'bg-rose-500',
  };
};

export const formatDate = (dateStr?: string): string => {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
};
