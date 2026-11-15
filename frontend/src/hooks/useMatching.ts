import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { runMatching, getResults, getCandidateAnalysis } from '../api/matching';
import type { ScoringMode } from '../types';
import toast from 'react-hot-toast';

export const useResults = (jobId: number) => {
  return useQuery({
    queryKey: ['results', jobId],
    queryFn: () => getResults(jobId),
    enabled: !isNaN(jobId) && jobId > 0,
  });
};

export const useCandidateAnalysis = (jobId: number, resumeId: number) => {
  return useQuery({
    queryKey: ['candidate-analysis', jobId, resumeId],
    queryFn: () => getCandidateAnalysis(jobId, resumeId),
    enabled: !isNaN(jobId) && jobId > 0 && !isNaN(resumeId) && resumeId > 0,
  });
};

export const useRunMatching = (jobId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scoringMode?: ScoringMode) => runMatching(jobId, scoringMode || 'standard'),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['results', jobId] });
      toast.success(`Matched & ranked ${data.length} candidate(s)!`);
    },
    onError: (error: Error) => {
      toast.error(`Matching error: ${error.message}`);
    },
  });
};
