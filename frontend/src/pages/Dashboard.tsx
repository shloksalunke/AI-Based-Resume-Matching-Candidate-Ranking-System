import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Briefcase, Trash2, ArrowRight, Award, Calendar, Layers } from 'lucide-react';
import { useJobs, useDeleteJob } from '../hooks/useJobs';
import { Button, Card, Badge, Spinner, EmptyState } from '../components/ui';
import { formatDate } from '../utils/formatters';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: jobs, isLoading, error } = useJobs();
  const deleteJobMutation = useDeleteJob();
  const [jobToDelete, setJobToDelete] = useState<number | null>(null);

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this job description and its match history?')) {
      setJobToDelete(id);
      deleteJobMutation.mutate(id, {
        onSettled: () => setJobToDelete(null),
      });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Job Descriptions
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage target roles, parse resume batches, and run explainable ranking algorithms.
          </p>
        </div>
        <Button
          onClick={() => navigate('/jobs/new')}
          icon={<Plus className="w-4 h-4" />}
          variant="primary"
          size="md"
        >
          Create New Job
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm mb-6">
          Failed to load job descriptions. Please verify backend server is running at http://127.0.0.1:8000.
        </div>
      )}

      {!isLoading && !error && (!jobs || jobs.length === 0) && (
        <EmptyState
          icon={<Briefcase className="w-12 h-12" />}
          title="No Job Descriptions Found"
          description="Create your first job description by pasting the role description or uploading a document."
          actionLabel="Create Job"
          onAction={() => navigate('/jobs/new')}
        />
      )}

      {!isLoading && jobs && jobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => {
            const reqSkills = job.required_skills || [];
            const coreSkills = job.core_skills || [];
            const displaySkills = reqSkills.slice(0, 4);
            const remainingCount = reqSkills.length - displaySkills.length;

            return (
              <Card
                key={job.id}
                hoverable
                onClick={() => navigate(`/jobs/${job.id}`)}
                className="flex flex-col justify-between group relative"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <h2 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                      {job.title}
                    </h2>
                    <button
                      onClick={(e) => handleDelete(e, job.id)}
                      disabled={jobToDelete === job.id}
                      title="Delete Job"
                      className="text-slate-400 hover:text-rose-600 p-1 rounded-md transition-colors"
                    >
                      {jobToDelete === job.id ? (
                        <Spinner size="sm" className="text-rose-600" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 mb-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1 font-medium bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                      <Award className="w-3.5 h-3.5 text-indigo-500" />
                      {job.min_experience > 0 ? `${job.min_experience}+ Yrs Exp` : 'Any Experience'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      {formatDate(job.created_at)}
                    </span>
                  </div>

                  {coreSkills.length > 0 && (
                    <div className="mb-3">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                        <Layers className="w-3 h-3 text-indigo-500" /> Core Weighted Skills
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {coreSkills.map((s) => (
                          <Badge key={s} variant="purple" size="sm">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="mb-4">
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Required Skills ({reqSkills.length})
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {displaySkills.map((s) => (
                        <span
                          key={s}
                          className="text-xs bg-slate-50 border border-slate-200 text-slate-700 px-2 py-0.5 rounded"
                        >
                          {s}
                        </span>
                      ))}
                      {remainingCount > 0 && (
                        <span className="text-xs text-slate-500 px-1.5 py-0.5 self-center font-medium">
                          +{remainingCount} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between mt-auto">
                  <span className="text-xs font-semibold text-indigo-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    View Details & Candidates <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
