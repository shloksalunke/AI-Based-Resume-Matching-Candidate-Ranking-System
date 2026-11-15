import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getResumes, uploadResumes, deleteResume } from '../api/resumes';
import toast from 'react-hot-toast';

export const useResumes = () => {
  return useQuery({
    queryKey: ['resumes'],
    queryFn: getResumes,
  });
};

export const useUploadResumes = (onProgress?: (percent: number) => void) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (files: File[]) => uploadResumes(files, onProgress),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      if (data.successful > 0 && data.failed === 0) {
        toast.success(`Successfully uploaded ${data.successful} resume(s)!`);
      } else if (data.successful > 0 && data.failed > 0) {
        toast(`Uploaded ${data.successful} resume(s), ${data.failed} failed.`, { icon: '⚠️' });
      } else {
        toast.error('All resume uploads failed. Check file types and sizes.');
      }
    },
    onError: (error: Error) => {
      toast.error(`Upload error: ${error.message}`);
    },
  });
};

export const useDeleteResume = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      toast.success('Resume deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete resume: ${error.message}`);
    },
  });
};
