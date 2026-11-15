import { apiClient } from './client';
import type { CandidateAiSummary, CandidateAiEvaluation, LlmStatus } from '../types';

export const getLlmStatus = async (): Promise<LlmStatus> => {
  const response = await apiClient.get<LlmStatus>('/api/llm/status');
  return response.data;
};

export const generateAiSummary = async (
  jobId: number,
  resumeId: number
): Promise<CandidateAiSummary> => {
  const response = await apiClient.post<CandidateAiSummary>(
    `/api/jobs/${jobId}/results/${resumeId}/ai-summary`
  );
  return response.data;
};

export const runCandidateAiReview = async (
  jobId: number,
  resumeId: number,
  refresh: boolean = false
): Promise<CandidateAiEvaluation> => {
  const response = await apiClient.post<CandidateAiEvaluation>(
    `/api/jobs/${jobId}/results/${resumeId}/ai-review`,
    null,
    { params: { refresh } }
  );
  return response.data;
};
