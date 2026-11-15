import React from 'react';
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useQueries } from '@tanstack/react-query';
import { ArrowLeft, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { getCandidateAnalysis } from '../api/matching';
import { useJob } from '../hooks/useJobs';
import {
  Button,
  Card,
  Spinner,
  ScoreBar,
  SkillChip,
  Badge,
} from '../components/ui';
import { ScoreGauge } from '../components/candidate/ScoreGauge';
import type { JobMatchDetailedResponse } from '../types';

export const Compare: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const jobId = Number(id);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const idsParam = searchParams.get('ids') || '';
  const resumeIds = idsParam
    .split(',')
    .map((s) => Number(s.trim()))
    .filter((n) => !isNaN(n) && n > 0);

  const { data: job } = useJob(jobId);

  // Parallel fetch for all selected candidates
  const candidateQueries = useQueries({
    queries: resumeIds.map((rId) => ({
      queryKey: ['candidate-analysis', jobId, rId],
      queryFn: () => getCandidateAnalysis(jobId, rId),
    })),
  });

  const isLoading = candidateQueries.some((q) => q.isLoading);
  const isError = candidateQueries.some((q) => q.isError);

  if (resumeIds.length < 2) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <Card className="py-12">
          <h2 className="text-xl font-bold text-slate-800 mb-2">Insufficient Candidates to Compare</h2>
          <p className="text-sm text-slate-500 mb-6">
            Please select at least 2 candidates from the rankings page to perform a side-by-side comparison.
          </p>
          <Button variant="primary" onClick={() => navigate(`/jobs/${jobId}/results`)}>
            Back to Rankings
          </Button>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <Card className="py-12 border-rose-200 bg-rose-50/40">
          <h2 className="text-xl font-bold text-slate-800 mb-2">Failed to Load Candidate Details</h2>
          <p className="text-sm text-slate-500 mb-6">
            An error occurred while loading comparison data for the selected candidates.
          </p>
          <Button variant="primary" onClick={() => navigate(`/jobs/${jobId}/results`)}>
            Back to Rankings
          </Button>
        </Card>
      </div>
    );
  }

  const candidatesData: JobMatchDetailedResponse[] = candidateQueries
    .map((q) => q.data)
    .filter((d): d is JobMatchDetailedResponse => d !== undefined);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider">
            <Link to="/" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <Link to={`/jobs/${jobId}/results`} className="hover:underline">Rankings</Link>
            <span>/</span>
            <span>Compare</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Side-by-Side Comparison
          </h1>
          <p className="text-xs text-slate-500">
            Target Role: <strong className="text-slate-800">{job?.title || `Job #${jobId}`}</strong>
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/jobs/${jobId}/results`)}
          icon={<ArrowLeft className="w-4 h-4" />}
        >
          Back to Rankings
        </Button>
      </div>

      {/* Comparison Grid */}
      <div
        className={`grid grid-cols-1 md:grid-cols-${candidatesData.length} gap-6 items-start`}
        style={{
          gridTemplateColumns: `repeat(${candidatesData.length}, minmax(0, 1fr))`,
        }}
      >
        {candidatesData.map((item) => {
          const { candidate, overall_score, score_breakdown, matched_skills, partially_matched_skills, missing_skills, reasons } = item;

          return (
            <Card key={candidate.resume_id} className="space-y-6 flex flex-col justify-between">
              <div>
                {/* Candidate Basic Info */}
                <div className="pb-4 border-b border-slate-100">
                  <h2 className="text-xl font-bold text-slate-900 truncate">
                    {candidate.name || candidate.filename}
                  </h2>
                  <p className="text-xs text-slate-400 font-mono truncate">{candidate.filename}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="default" size="sm">
                      {candidate.total_experience_years > 0
                        ? candidate.total_experience_years < 1
                          ? `${Math.max(1, Math.round(candidate.total_experience_years * 12))} mo exp`
                          : `${candidate.total_experience_years.toFixed(1)} yrs exp`
                        : 'Fresher'}
                    </Badge>
                    {candidate.education && candidate.education.length > 0 && (
                      <Badge variant="info" size="sm">
                        {candidate.education[0]?.degree || 'Higher Ed'}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Score Gauge */}
                <div className="py-4 flex justify-center">
                  <ScoreGauge score={overall_score} size={130} />
                </div>

                {/* Score Breakdown Bars */}
                <div className="space-y-3 p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs">
                  <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider">
                    Component Breakdown
                  </span>
                  <div>
                    <div className="flex justify-between text-slate-600 mb-1">
                      <span>Skills Match</span>
                      <span className="font-semibold">{score_breakdown.skills?.score || 0} / 40 pts</span>
                    </div>
                    <ScoreBar score={((score_breakdown.skills?.score || 0) / 40) * 100} showText={false} size="sm" />
                  </div>
                  <div>
                    <div className="flex justify-between text-slate-600 mb-1">
                      <span>Semantic Fit</span>
                      <span className="font-semibold">{score_breakdown.semantic?.score || 0} / 25 pts</span>
                    </div>
                    <ScoreBar score={((score_breakdown.semantic?.score || 0) / 25) * 100} showText={false} size="sm" />
                  </div>
                  <div>
                    <div className="flex justify-between text-slate-600 mb-1">
                      <span>Experience</span>
                      <span className="font-semibold">{score_breakdown.experience?.score || 0} / 20 pts</span>
                    </div>
                    <ScoreBar score={((score_breakdown.experience?.score || 0) / 20) * 100} showText={false} size="sm" />
                  </div>
                  <div>
                    <div className="flex justify-between text-slate-600 mb-1">
                      <span>Education</span>
                      <span className="font-semibold">{score_breakdown.education?.score || 0} / 10 pts</span>
                    </div>
                    <ScoreBar score={((score_breakdown.education?.score || 0) / 10) * 100} showText={false} size="sm" />
                  </div>
                  <div>
                    <div className="flex justify-between text-slate-600 mb-1">
                      <span>Portfolio/Certs</span>
                      <span className="font-semibold">{score_breakdown.relevance?.score || 0} / 5 pts</span>
                    </div>
                    <ScoreBar score={((score_breakdown.relevance?.score || 0) / 5) * 100} showText={false} size="sm" />
                  </div>
                </div>

                {/* Matched Skills */}
                <div className="mt-5 space-y-3">
                  <div>
                    <span className="text-xs font-bold text-emerald-700 block mb-1.5 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" /> Matched Skills ({matched_skills.length})
                    </span>
                    <div className="flex flex-wrap gap-1 max-h-28 overflow-y-auto pr-1">
                      {matched_skills.map((s) => (
                        <SkillChip key={s} name={s} status="matched" size="sm" />
                      ))}
                    </div>
                  </div>

                  {partially_matched_skills.length > 0 && (
                    <div>
                      <span className="text-xs font-bold text-amber-700 block mb-1.5 flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> Partial Matches ({partially_matched_skills.length})
                      </span>
                      <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto pr-1">
                        {partially_matched_skills.map((s) => (
                          <SkillChip key={s} name={s} status="partial" size="sm" />
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <span className="text-xs font-bold text-rose-700 block mb-1.5 flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> Missing Skills ({missing_skills.length})
                    </span>
                    <div className="flex flex-wrap gap-1 max-h-28 overflow-y-auto pr-1">
                      {missing_skills.map((s) => (
                        <SkillChip key={s} name={s} status="missing" size="sm" />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Key Reason Preview */}
                <div className="mt-5 pt-4 border-t border-slate-100">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                    Scoring Insights
                  </span>
                  <div className="space-y-1 text-xs text-slate-600">
                    {reasons.slice(0, 3).map((r, i) => (
                      <p key={i} className="line-clamp-2">• {r}</p>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => navigate(`/jobs/${jobId}/candidates/${candidate.resume_id}`)}
                >
                  Full Profile Analysis
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
