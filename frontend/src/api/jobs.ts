import { apiClient } from './client';
import type { JobDescription } from '../types';

export const getJobs = async (): Promise<JobDescription[]> => {
  const response = await apiClient.get<JobDescription[]>('/api/jobs');
  return response.data;
};

export const getJob = async (id: number): Promise<JobDescription> => {
  const response = await apiClient.get<JobDescription>(`/api/jobs/${id}`);
  return response.data;
};

export const createJob = async (formData: FormData): Promise<JobDescription> => {
  const response = await apiClient.post<JobDescription>('/api/jobs', formData);
  return response.data;
};

export const deleteJob = async (id: number): Promise<{ message: string }> => {
  const response = await apiClient.delete<{ message: string }>(`/api/jobs/${id}`);
  return response.data;
};
