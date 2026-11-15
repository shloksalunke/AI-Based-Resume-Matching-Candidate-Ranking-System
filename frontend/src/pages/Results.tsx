import React, { useState, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowUpDown,
  Filter,
  Play,
  Columns,
  ArrowRight,
  SlidersHorizontal,
  Users,
  Award,
  TrendingUp,
  CheckCircle2,
  Search,
  Download,
  X,
} from 'lucide-react';
import { useResults, useRunMatching } from '../hooks/useMatching';
import { useJob } from '../hooks/useJobs';
import {
  Button,
  Card,
  Spinner,
  EmptyState,
  ScoreBar,
  SkillChip,
} from '../components/ui';

type SortField = 'rank' | 'name' | 'experience' | 'score';
type SortOrder = 'asc' | 'desc';

export const Results: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const jobId = Number(id);
  const navigate = useNavigate();

  const { data: job } = useJob(jobId);
  const { data: results, isLoading, error } = useResults(jobId);
  const runMatchingMutation = useRunMatching(jobId);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [selectedResumeIds, setSelectedResumeIds] = useState<number[]>([]);

  // KPI Metrics
  const stats = useMemo(() => {
    if (!results || results.length === 0) {
      return { total: 0, topScore: 0, avgScore: 0, strongMatches: 0 };
    }
    const total = results.length;
    const scores = results.map((r) => r.overall_score);
    const topScore = Math.max(...scores);
    const avgScore = Math.round(scores.reduce((a, b) => a + b, 0) / total);
    const strongMatches = results.filter((r) => r.overall_score >= 65).length;
    return { total, topScore, avgScore, strongMatches };
  }, [results]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder(field === 'score' ? 'desc' : 'asc');
    }
  };

  const handleSelectCandidate = (resumeId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedResumeIds((prev) => {
      if (prev.includes(resumeId)) {
        return prev.filter((id) => id !== resumeId);
      }
      if (prev.length >= 3) {
        alert('You can select a maximum of 3 candidates to compare side-by-side.');
        return prev;
      }
      return [...prev, resumeId];
    });
  };

  const filteredAndSortedResults = useMemo(() => {
    if (!results) return [];

    let filtered = results.filter((item) => item.overall_score >= minScoreFilter);

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      filtered = filtered.filter((item) => {
        const nameMatch = (item.name || item.filename).toLowerCase().includes(q);
        const emailMatch = (item.email || '').toLowerCase().includes(q);
        const skillMatch = (item.matched_skills || []).some((s) => s.toLowerCase().includes(q));
        return nameMatch || emailMatch || skillMatch;
      });
    }

    return filtered.sort((a, b) => {
      let comparison = 0;
      if (sortField === 'rank') {
        comparison = a.rank - b.rank;
      } else if (sortField === 'name') {
        const nameA = a.name || a.filename;
        const nameB = b.name || b.filename;
        comparison = nameA.localeCompare(nameB);
      } else if (sortField === 'experience') {
        comparison = a.total_experience_years - b.total_experience_years;
      } else if (sortField === 'score') {
        comparison = a.overall_score - b.overall_score;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [results, minScoreFilter, searchQuery, sortField, sortOrder]);

  const handleNavigateToCompare = () => {
    if (selectedResumeIds.length < 2) return;
    navigate(`/jobs/${jobId}/compare?ids=${selectedResumeIds.join(',')}`);
  };

  const handleExportCSV = () => {
    if (!results || results.length === 0) return;
    const headers = ['Rank', 'Candidate Name', 'Email', 'Experience', 'Match Score (%)', 'Matched Skills'];
    const rows = results.map((r) => [
      r.rank,
      `"${(r.name || r.filename).replace(/"/g, '""')}"`,
      `"${(r.email || '').replace(/"/g, '""')}"`,
      r.total_experience_years > 0 ? `${r.total_experience_years.toFixed(1)} yrs` : 'Fresher',
      r.overall_score.toFixed(1),
      `"${(r.matched_skills || []).join(', ')}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${(job?.title || 'job').toLowerCase().replace(/\s+/g, '_')}_rankings.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-1">
            <Link to="/" className="hover:underline">Dashboard</Link>
            <span>/</span>
            <Link to={`/jobs/${jobId}`} className="hover:underline">{job?.title || `Job #${jobId}`}</Link>
            <span>/</span>
            <span>Rankings</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Ranked Candidate Leaderboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Explainable AI matching based on skills (40%), semantics (25%), experience (20%), education (10%), and portfolio (5%).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {results && results.length > 0 && (
            <Button
              variant="outline"
              size="md"
              icon={<Download className="w-4 h-4" />}
              onClick={handleExportCSV}
              title="Download results as CSV spreadsheet"
            >
              Export CSV
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => navigate(`/jobs/${jobId}`)}
          >
            Manage Resumes
          </Button>
          <Button
            variant="primary"
            icon={<Play className="w-4 h-4 fill-current" />}
            isLoading={runMatchingMutation.isPending}
            onClick={() => runMatchingMutation.mutate()}
          >
            Re-run Match
          </Button>
        </div>
      </div>

      {/* KPI Metric Summary Cards */}
      {results && results.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">Evaluated</span>
              <span className="text-xl font-extrabold text-slate-900">{stats.total} Resumes</span>
            </div>
          </div>

          <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 flex-shrink-0">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">Top Match</span>
              <span className="text-xl font-extrabold text-amber-700">{stats.topScore.toFixed(1)}%</span>
            </div>
          </div>

          <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">Average Score</span>
              <span className="text-xl font-extrabold text-slate-900">{stats.avgScore}%</span>
            </div>
          </div>

          <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 flex-shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">Strong Fit (&ge;65%)</span>
              <span className="text-xl font-extrabold text-emerald-700">{stats.strongMatches} Candidates</span>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Compare Action Toolbar */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        {/* Live Search Box */}
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by candidate name or skill..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-slate-50/50"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Min Score Slider */}
        <div className="flex items-center gap-3 flex-1 max-w-md">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 whitespace-nowrap">
            <SlidersHorizontal className="w-4 h-4 text-slate-400" />
            Min Score Filter:
          </div>
          <input
            type="range"
            min="0"
            max="90"
            step="5"
            value={minScoreFilter}
            onChange={(e) => setMinScoreFilter(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer h-2 bg-slate-100 rounded-lg"
          />
          <span className="text-xs font-bold font-mono px-2 py-0.5 bg-slate-100 text-slate-700 rounded min-w-[50px] text-center">
            {minScoreFilter}%+
          </span>
        </div>

        {/* Compare Selection Pill */}
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs text-slate-500 font-medium">
            Selected: <strong className="text-slate-800">{selectedResumeIds.length}/3</strong>
          </span>
          <Button
            variant={selectedResumeIds.length >= 2 ? 'primary' : 'secondary'}
            size="sm"
            disabled={selectedResumeIds.length < 2}
            onClick={handleNavigateToCompare}
            icon={<Columns className="w-3.5 h-3.5" />}
          >
            Compare Selected ({selectedResumeIds.length})
          </Button>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
          Failed to load candidate match results.
        </div>
      )}

      {!isLoading && (!results || results.length === 0) && (
        <EmptyState
          icon={<Filter className="w-12 h-12" />}
          title="No Match Results Available"
          description="Run the matching engine to evaluate and rank all uploaded candidates against this role."
          actionLabel="Run Matching Now"
          onAction={() => runMatchingMutation.mutate()}
        />
      )}

      {/* Results Table */}
      {!isLoading && results && results.length > 0 && (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/90 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4 w-12 text-center">
                    <span className="sr-only">Select</span>
                  </th>
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-slate-800 transition-colors w-24"
                    onClick={() => handleSort('rank')}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Rank</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-slate-800 transition-colors"
                    onClick={() => handleSort('name')}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Candidate</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-slate-800 transition-colors w-32"
                    onClick={() => handleSort('experience')}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Experience</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-slate-800 transition-colors min-w-[220px]"
                    onClick={() => handleSort('score')}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Match % & Fit</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th className="py-3 px-4">Matched Skills</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredAndSortedResults.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-slate-400">
                      No candidates match your current search and filters.
                    </td>
                  </tr>
                ) : (
                  filteredAndSortedResults.map((item) => {
                    const isSelected = selectedResumeIds.includes(item.resume_id);
                    const matched = item.matched_skills || [];
                    const displaySkills = matched.slice(0, 4);
                    const remainingCount = matched.length - displaySkills.length;

                    // Rank Medal Badge
                    const rankBadge =
                      item.rank === 1 ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300 shadow-xs">
                          🥇 #1
                        </span>
                      ) : item.rank === 2 ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-200 text-slate-800 border border-slate-300">
                          🥈 #2
                        </span>
                      ) : item.rank === 3 ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-900 border border-amber-200">
                          🥉 #3
                        </span>
                      ) : (
                        <span className="font-bold font-mono text-slate-500 pl-1">
                          #{item.rank}
                        </span>
                      );

                    // Fit Tier
                    const fitTier =
                      item.overall_score >= 70 ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 whitespace-nowrap">
                          Strong Fit
                        </span>
                      ) : item.overall_score >= 50 ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-200 whitespace-nowrap">
                          Moderate Fit
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 border border-slate-200 whitespace-nowrap">
                          Low Fit
                        </span>
                      );

                    return (
                      <tr
                        key={item.match_id}
                        onClick={() => navigate(`/jobs/${jobId}/candidates/${item.resume_id}`)}
                        className={`hover:bg-indigo-50/40 cursor-pointer transition-colors ${
                          isSelected ? 'bg-indigo-50/60' : ''
                        }`}
                      >
                        <td className="py-3 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => handleSelectCandidate(item.resume_id, e as unknown as React.MouseEvent)}
                            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer h-4 w-4"
                          />
                        </td>
                        <td className="py-3 px-4">
                          {rankBadge}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-900 hover:text-indigo-600 transition-colors">
                            {item.name || item.filename}
                          </div>
                          {item.email && (
                            <div className="text-[11px] text-slate-400">{item.email}</div>
                          )}
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-700">
                          {item.total_experience_years > 0
                            ? item.total_experience_years < 1
                              ? `${Math.max(1, Math.round(item.total_experience_years * 12))} mo`
                              : `${item.total_experience_years.toFixed(1)} yrs`
                            : 'Fresher'}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="flex-1">
                              <ScoreBar score={item.overall_score} size="md" />
                            </div>
                            {fitTier}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-wrap gap-1 items-center max-w-xs">
                            {displaySkills.map((s) => (
                              <SkillChip key={s} name={s} status="matched" size="sm" />
                            ))}
                            {remainingCount > 0 && (
                              <span className="text-[11px] text-slate-500 font-medium">
                                +{remainingCount} more
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span className="text-xs font-semibold text-indigo-600 inline-flex items-center gap-1 hover:translate-x-0.5 transition-transform">
                            Analysis <ArrowRight className="w-3.5 h-3.5" />
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
