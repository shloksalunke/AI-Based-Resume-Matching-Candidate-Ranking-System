import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { Navbar } from './components/ui/Navbar';
import {
  Dashboard,
  CreateJob,
  JobDetail,
  Results,
  CandidateDetail,
  Compare,
} from './pages';

// Create a single stable QueryClient instance with reasonable cache timeouts
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/jobs/new" element={<CreateJob />} />
              <Route path="/jobs/:id" element={<JobDetail />} />
              <Route path="/jobs/:id/results" element={<Results />} />
              <Route path="/jobs/:id/candidates/:resumeId" element={<CandidateDetail />} />
              <Route path="/jobs/:id/compare" element={<Compare />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
            AI-Based Resume Matching & Candidate Ranking System &bull; 100% Offline AI (all-MiniLM-L6-v2 + spaCy)
          </footer>
        </div>
        <Toaster position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
