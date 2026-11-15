import { apiClient } from './client';
import type { Resume, ResumeUploadBatchResponse } from '../types';

export const getResumes = async (): Promise<Resume[]> => {
  const response = await apiClient.get<Resume[]>('/api/resumes');
  return response.data;
};

export const getResume = async (id: number): Promise<Resume> => {
  const response = await apiClient.get<Resume>(`/api/resumes/${id}`);
  return response.data;
};

export const uploadResumes = async (
  files: File[],
  onProgress?: (percentage: number) => void
): Promise<ResumeUploadBatchResponse> => {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }

  const response = await apiClient.post<ResumeUploadBatchResponse>(
    '/api/resumes/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    }
  );

  return response.data;
};

export const deleteResume = async (id: number): Promise<{ message: string }> => {
  const response = await apiClient.delete<{ message: string }>(`/api/resumes/${id}`);
  return response.data;
};
