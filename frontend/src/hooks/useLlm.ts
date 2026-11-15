import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLlmStatus, generateAiSummary, runCandidateAiReview } from '../api/llm';
import toast from 'react-hot-toast';

export const useLlmStatus = () => {
  return useQuery({
    queryKey: ['llm-status'],
    queryFn: getLlmStatus,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
};

export const useAiSummary = (jobId: number, resumeId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateAiSummary(jobId, resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-analysis', jobId, resumeId] });
      toast.success('AI executive summary generated successfully!');
    },
    onError: (error: Error) => {
      toast.error(`AI summary generation failed: ${error.message}`);
    },
  });
};

export const useAiReview = (jobId: number, resumeId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (refresh: boolean = true) => runCandidateAiReview(jobId, resumeId, refresh),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['candidate-analysis', jobId, resumeId] });
      queryClient.invalidateQueries({ queryKey: ['results', jobId] });
      if (data.error) {
        toast.error(`AI review note: ${data.error}`);
      } else {
        toast.success('AI evaluation completed successfully!');
      }
    },
    onError: (error: Error) => {
      toast.error(`AI review failed: ${error.message}`);
    },
  });
};
