import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  Play,
  CheckCircle2,
  AlertCircle,
  Layers,
  ArrowRight,
  ListOrdered,
  UserCheck,
} from 'lucide-react';
import { useJob } from '../hooks/useJobs';
import { useResumes, useUploadResumes, useDeleteResume } from '../hooks/useResumes';
import { useRunMatching, useResults } from '../hooks/useMatching';
import {
  Button,
  Card,
  Badge,
  Spinner,
  SkillChip,
  FileDropzone,
} from '../components/ui';
import type { ResumeUploadBatchResponse } from '../types';

export const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const jobId = Number(id);
  const navigate = useNavigate();

  const { data: job, isLoading: isJobLoading, error: jobError } = useJob(jobId);
  const { data: resumes, isLoading: isResumesLoading } = useResumes();
  const { data: results } = useResults(jobId);

  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [queuedFiles, setQueuedFiles] = useState<File[]>([]);
  const [lastUploadBatch, setLastUploadBatch] = useState<ResumeUploadBatchResponse | null>(null);

  const uploadMutation = useUploadResumes((percent) => setUploadProgress(percent));
  const runMatchingMutation = useRunMatching(jobId);
  const deleteResumeMutation = useDeleteResume();

  const handleUploadSubmit = () => {
    if (queuedFiles.length === 0) return;
    uploadMutation.mutate(queuedFiles, {
      onSuccess: (batchResp) => {
        setLastUploadBatch(batchResp);
        setQueuedFiles([]);
        setUploadProgress(null);
      },
      onError: () => {
        setUploadProgress(null);
      },
    });
  };

  const handleRunMatching = () => {
    runMatchingMutation.mutate(undefined, {
      onSuccess: () => {
        navigate(`/jobs/${jobId}/results`);
      },
    });
  };

  if (isJobLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (jobError || !job) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <Card className="border-rose-200 bg-rose-50/40 text-center py-10">
          <AlertCircle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-800">Job Description Not Found</h2>
          <p className="text-sm text-slate-500 mb-4">The requested job could not be loaded.</p>
          <Button variant="primary" onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  const hasMatches = results && results.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-1">
            <Link to="/" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <span>Job #{job.id}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {job.title}
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {hasMatches && (
            <Button
              variant="outline"
              icon={<ListOrdered className="w-4 h-4" />}
              onClick={() => navigate(`/jobs/${job.id}/results`)}
            >
              View Existing Rankings ({results.length})
            </Button>
          )}

          <Button
            variant="primary"
            icon={<Play className="w-4 h-4 fill-current" />}
            isLoading={runMatchingMutation.isPending}
            onClick={handleRunMatching}
            disabled={!resumes || resumes.length === 0}
          >
            {runMatchingMutation.isPending ? 'Matching Resumes...' : 'Run Matching Engine'}
          </Button>
        </div>
      </div>

      {/* Grid: Job Description Summary & Upload Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Job Description Summary (1 Col) */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="sticky top-24">
            <h2 className="text-base font-bold text-slate-900 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-600" />
              Target Job Requirements
            </h2>

            <div className="space-y-5 text-sm">
              <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                <span className="text-xs text-slate-500 font-medium">Minimum Experience</span>
                <span className="font-bold text-slate-800">
                  {job.min_experience > 0 ? `${job.min_experience}+ Years` : 'None specified'}
                </span>
              </div>

              {job.education && job.education.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-slate-500 block mb-1.5">Education Desired</span>
                  <div className="flex flex-wrap gap-1">
                    {job.education.map((edu) => (
                      <Badge key={edu} variant="info" size="sm">
                        {edu}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {job.core_skills && job.core_skills.length > 0 && (
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-1.5">
                    <span className="flex items-center gap-1 text-indigo-700">
                      <Layers className="w-3.5 h-3.5" /> Core Skills (3x Weight)
                    </span>
                    <span className="text-[10px] text-amber-600 font-normal">Cap &le;30% if missing</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {job.core_skills.map((s) => (
                      <Badge key={s} variant="purple" size="sm">
                        ⭐ {s}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <span className="text-xs font-semibold text-slate-500 block mb-1.5">
                  Required Skills ({job.required_skills?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1">
                  {job.required_skills?.map((s) => (
                    <SkillChip key={s} name={s} status="default" size="sm" />
                  ))}
                </div>
              </div>

              {job.preferred_skills && job.preferred_skills.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-slate-500 block mb-1.5">
                    Preferred Skills ({job.preferred_skills.length})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {job.preferred_skills.map((s) => (
                      <SkillChip key={s} name={s} status="default" size="sm" />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Resume Uploader & Library (2 Cols) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Upload Card */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Upload Resumes for Matching</h2>
                <p className="text-xs text-slate-500">
                  Batch upload PDF or DOCX candidate resumes (up to 20 files, max 5MB each).
                </p>
              </div>
            </div>

            <FileDropzone
              acceptedExtensions={['.pdf', '.docx']}
              multiple={true}
              onFilesSelected={(files) => setQueuedFiles(files)}
              disabled={uploadMutation.isPending}
            />

            {uploadProgress !== null && (
              <div className="mt-4">
                <div className="flex justify-between text-xs text-slate-600 font-medium mb-1">
                  <span>Uploading files to server...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {queuedFiles.length > 0 && (
              <div className="mt-4 flex justify-end">
                <Button
                  onClick={handleUploadSubmit}
                  variant="primary"
                  isLoading={uploadMutation.isPending}
                >
                  Upload {queuedFiles.length} File{queuedFiles.length > 1 ? 's' : ''}
                </Button>
              </div>
            )}

            {/* Batch Upload Results Report */}
            {lastUploadBatch && (
              <div className="mt-6 p-4 rounded-xl border border-slate-200 bg-slate-50/70">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Last Batch Upload Summary ({lastUploadBatch.successful} Successful, {lastUploadBatch.failed} Failed)
                </h3>
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1 text-xs">
                  {lastUploadBatch.results.map((res, i) => (
                    <div
                      key={`${res.filename}-${i}`}
                      className={`flex items-center justify-between p-2 rounded-lg border ${
                        res.status === 'success'
                          ? 'bg-emerald-50/50 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50/50 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        {res.status === 'success' ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                        )}
                        <span className="font-medium truncate">{res.filename}</span>
                        {res.candidate_name && (
                          <span className="text-slate-500 font-normal">({res.candidate_name})</span>
                        )}
                      </div>
                      <span className="font-semibold text-[11px]">
                        {res.status === 'success' ? 'PARSED' : res.error_message || 'FAILED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Uploaded Resumes Library */}
          <Card>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-indigo-600" />
                <h2 className="text-base font-bold text-slate-900">
                  Uploaded Candidate Pool ({resumes?.length || 0})
                </h2>
              </div>
              {hasMatches && (
                <Link
                  to={`/jobs/${job.id}/results`}
                  className="text-xs font-semibold text-indigo-600 hover:underline flex items-center gap-1"
                >
                  View Ranked Table <ArrowRight className="w-3 h-3" />
                </Link>
              )}
            </div>

            {isResumesLoading && (
              <div className="flex justify-center py-8">
                <Spinner size="md" />
              </div>
            )}

            {!isResumesLoading && (!resumes || resumes.length === 0) && (
              <div className="text-center py-8 text-slate-400 text-sm">
                No resumes uploaded yet. Upload resumes above to test matching.
              </div>
            )}

            {!isResumesLoading && resumes && resumes.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3 rounded-l-lg">Candidate Name</th>
                      <th className="py-2.5 px-3">Experience</th>
                      <th className="py-2.5 px-3">Parsed Skills</th>
                      <th className="py-2.5 px-3">File</th>
                      <th className="py-2.5 px-3 text-right rounded-r-lg">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {resumes.map((res) => (
                      <tr key={res.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-2.5 px-3 font-semibold text-slate-800">
                          {res.name || 'Unnamed Candidate'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-600">
                          {res.total_experience_years > 0
                            ? `${res.total_experience_years.toFixed(1)} yrs`
                            : 'Fresher'}
                        </td>
                        <td className="py-2.5 px-3 text-slate-600">
                          {res.skills?.length || 0} skills detected
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 font-mono truncate max-w-xs">
                          {res.filename}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => {
                              if (confirm(`Delete resume ${res.filename}?`)) {
                                deleteResumeMutation.mutate(res.id);
                              }
                            }}
                            className="text-slate-400 hover:text-rose-600 p-1"
                            title="Delete Resume"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
