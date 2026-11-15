import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Mail,
  Phone,
  Briefcase,
  GraduationCap,
  Award,
  FolderGit2,
  HelpCircle,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Layers,
} from 'lucide-react';
import { useCandidateAnalysis } from '../hooks/useMatching';
import {
  Button,
  Card,
  Badge,
  Spinner,
  SkillChip,
} from '../components/ui';
import { ScoreGauge } from '../components/candidate/ScoreGauge';
import { BreakdownChart } from '../components/candidate/BreakdownChart';

export const CandidateDetail: React.FC = () => {
  const { id, resumeId } = useParams<{ id: string; resumeId: string }>();
  const jobId = Number(id);
  const rId = Number(resumeId);
  const navigate = useNavigate();

  const { data: analysis, isLoading, error } = useCandidateAnalysis(jobId, rId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <Card className="text-center py-10 border-rose-200 bg-rose-50/40">
          <h2 className="text-lg font-bold text-slate-800 mb-2">Candidate Analysis Not Found</h2>
          <p className="text-sm text-slate-500 mb-4">
            Could not retrieve evaluation results for this resume and job pairing.
          </p>
          <Button variant="primary" onClick={() => navigate(`/jobs/${jobId}/results`)}>
            Back to Results
          </Button>
        </Card>
      </div>
    );
  }

  const { candidate, job, overall_score, score_breakdown, matched_skills, partially_matched_skills, missing_skills, reasons } = analysis;

  const meetsExperience = candidate.total_experience_years >= job.min_experience;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider">
          <Link to="/" className="hover:underline">Dashboard</Link>
          <span>/</span>
          <Link to={`/jobs/${jobId}`} className="hover:underline">{job.title}</Link>
          <span>/</span>
          <Link to={`/jobs/${jobId}/results`} className="hover:underline">Rankings</Link>
          <span>/</span>
          <span className="text-slate-500">{candidate.name || candidate.filename}</span>
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

      {/* Top Banner: Candidate Info & Score Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Candidate Profile Card */}
        <Card className="lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                  {candidate.name || 'Unnamed Candidate'}
                </h1>
                <p className="text-xs font-mono text-slate-400 mt-0.5">{candidate.filename}</p>
              </div>
              <Badge variant="purple" size="md">
                Role: {job.title}
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
              <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <Mail className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                <span className="truncate">{candidate.email || 'Email not detected'}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <Phone className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                <span className="truncate">{candidate.phone || 'Phone not detected'}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <Clock className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                <span>
                  {candidate.total_experience_years > 0
                    ? candidate.total_experience_years < 1
                      ? `${Math.max(1, Math.round(candidate.total_experience_years * 12))} mo exp`
                      : `${candidate.total_experience_years.toFixed(1)} yrs exp`
                    : 'Fresher'}
                </span>
              </div>
            </div>
          </div>

          {/* Experience Comparison Quick Metric */}
          <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-200/80 flex items-center justify-between text-xs mt-2">
            <div className="flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-indigo-600" />
              <span className="font-semibold text-slate-700">Experience Requirement Check:</span>
            </div>
            <div>
              {job.min_experience <= 0 ? (
                <span className="text-emerald-700 font-semibold">No min exp required</span>
              ) : meetsExperience ? (
                <span className="text-emerald-700 font-bold flex items-center gap-1">
                  ✓ Meets Requirement ({candidate.total_experience_years < 1 ? `${Math.max(1, Math.round(candidate.total_experience_years * 12))} mo` : `${candidate.total_experience_years.toFixed(1)} yrs`} vs {job.min_experience.toFixed(1)} yrs required)
                </span>
              ) : (
                <span className="text-amber-700 font-bold flex items-center gap-1">
                  ⚠ Shortfall ({candidate.total_experience_years < 1 ? `${Math.max(1, Math.round(candidate.total_experience_years * 12))} mo` : `${candidate.total_experience_years.toFixed(1)} yrs`} vs {job.min_experience.toFixed(1)} yrs required)
                </span>
              )}
            </div>
          </div>
        </Card>

        {/* Score Gauge Card */}
        <Card className="flex flex-col items-center justify-center text-center">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
            Overall Match Index
          </span>
          <ScoreGauge score={overall_score} size={150} />
          <span className="text-[11px] text-slate-400 mt-2">Total Explainable Score (100 pts max)</span>
        </Card>
      </div>

      {/* 5-Component Breakdown Bar Chart */}
      <Card>
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-600" />
              Scoring Components Breakdown
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Comparison of earned points against maximum component weights.
            </p>
          </div>
        </div>
        <BreakdownChart breakdown={score_breakdown} />
      </Card>

      {/* Skills Match Status Section */}
      <Card>
        <h2 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100">
          Detailed Skills Analysis
        </h2>

        <div className="space-y-5">
          {/* Matched Skills */}
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-700 mb-2">
              <CheckCircle className="w-4 h-4" />
              Matched Skills ({matched_skills.length})
            </div>
            {matched_skills.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {matched_skills.map((s) => (
                  <SkillChip key={s} name={s} status="matched" />
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No exact skill matches detected.</p>
            )}
          </div>

          {/* Partially Matched Skills */}
          {partially_matched_skills.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-amber-700 mb-2">
                <AlertTriangle className="w-4 h-4" />
                Semantic / Partial Matches (0.5 Credit) ({partially_matched_skills.length})
              </div>
              <div className="flex flex-wrap gap-1.5">
                {partially_matched_skills.map((s) => (
                  <SkillChip key={s} name={s} status="partial" />
                ))}
              </div>
            </div>
          )}

          {/* Missing Skills */}
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-rose-700 mb-2">
              <XCircle className="w-4 h-4" />
              Missing Target Skills ({missing_skills.length})
            </div>
            {missing_skills.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {missing_skills.map((s) => (
                  <SkillChip key={s} name={s} status="missing" />
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No required skills missing!</p>
            )}
          </div>
        </div>
      </Card>

      {/* Why This Score? Reason Explanations */}
      <Card className="border-indigo-100 bg-indigo-50/20">
        <h2 className="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-indigo-600" />
          Why This Score? (Explainable Logic)
        </h2>
        <div className="space-y-2">
          {reasons.map((reason, i) => (
            <div
              key={i}
              className="flex items-start gap-2.5 p-2.5 bg-white rounded-lg border border-slate-200/80 text-xs text-slate-700"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 flex-shrink-0" />
              <span>{reason}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Extracted Profile Details (Experience, Education, Projects) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Work Experience */}
        <Card>
          <h2 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-indigo-600" />
            Work History
          </h2>
          {candidate.companies_and_designations && candidate.companies_and_designations.length > 0 ? (
            <div className="space-y-3">
              {candidate.companies_and_designations.map((exp, i) => (
                <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                  <div className="font-bold text-slate-800">{exp.designation || 'Role not specified'}</div>
                  <div className="text-indigo-600 font-medium">{exp.company || 'Company not specified'}</div>
                  {exp.dates && <div className="text-slate-400 mt-0.5">{exp.dates}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No structured roles detected.</p>
          )}
        </Card>

        {/* Education & Certifications */}
        <Card>
          <h2 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-indigo-600" />
            Education & Certifications
          </h2>

          <div className="space-y-4">
            <div>
              <span className="text-xs font-semibold text-slate-500 block mb-2">Education</span>
              {candidate.education && candidate.education.length > 0 ? (
                <div className="space-y-2">
                  {candidate.education.map((edu, i) => (
                    <div key={i} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                      <div className="font-bold text-slate-800">{edu.degree || 'Degree'}</div>
                      <div className="text-slate-500">{edu.institution || ''} {edu.year ? `(${edu.year})` : ''}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No formal education detected.</p>
              )}
            </div>

            {candidate.certifications && candidate.certifications.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-slate-500 block mb-2">Certifications</span>
                <div className="flex flex-wrap gap-1">
                  {candidate.certifications.map((cert, i) => (
                    <Badge key={i} variant="default" size="sm">
                      <Award className="w-3 h-3 text-amber-500 mr-1" />
                      {cert}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {candidate.projects && candidate.projects.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-slate-500 block mb-2">Projects</span>
                <div className="space-y-2">
                  {candidate.projects.map((proj, i) => (
                    <div key={i} className="p-2 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                      <div className="font-semibold text-slate-800 flex items-center gap-1">
                        <FolderGit2 className="w-3.5 h-3.5 text-indigo-500" />
                        {proj.title}
                      </div>
                      {proj.description && (
                        <p className="text-slate-500 mt-0.5 line-clamp-2">{proj.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
