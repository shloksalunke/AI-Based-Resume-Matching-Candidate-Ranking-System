import { apiClient } from './client';
import type { JobMatchRankedItem, JobMatchDetailedResponse, ScoringMode } from '../types';

export const runMatching = async (
  jobId: number,
  scoringMode: ScoringMode = 'standard'
): Promise<JobMatchRankedItem[]> => {
  const response = await apiClient.post<JobMatchRankedItem[]>(
    `/api/jobs/${jobId}/match`,
    null,
    { params: { scoring_mode: scoringMode } }
  );
  return response.data;
};

export const getResults = async (jobId: number): Promise<JobMatchRankedItem[]> => {
  const response = await apiClient.get<JobMatchRankedItem[]>(`/api/jobs/${jobId}/results`);
  return response.data;
};

export const getCandidateAnalysis = async (
  jobId: number,
  resumeId: number
): Promise<JobMatchDetailedResponse> => {
  const response = await apiClient.get<JobMatchDetailedResponse>(
    `/api/jobs/${jobId}/results/${resumeId}`
  );
  return response.data;
};
