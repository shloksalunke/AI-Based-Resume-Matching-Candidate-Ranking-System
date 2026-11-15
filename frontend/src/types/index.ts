// Explicit TypeScript interfaces matching backend Pydantic schemas exactly (no any)

export interface JobDescription {
  id: number;
  title: string;
  raw_text: string;
  required_skills: string[];
  core_skills: string[];
  preferred_skills: string[];
  min_experience: number;
  education: string[];
  keywords: string[];
  created_at?: string;
}

export interface CompanyRole {
  company?: string;
  designation?: string;
  dates?: string;
  duration_months?: number;
}

export interface EducationEntry {
  degree?: string;
  institution?: string;
  year?: string;
}

export interface ProjectEntry {
  title?: string;
  description?: string;
}

export interface Resume {
  id: number;
  filename: string;
  raw_text: string;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  skills: string[];
  total_experience_years: number;
  companies_and_designations: CompanyRole[];
  education: EducationEntry[];
  certifications: string[];
  projects: ProjectEntry[];
  created_at?: string;
}

export interface ResumeUploadResult {
  filename: string;
  status: 'success' | 'error';
  resume_id?: number | null;
  candidate_name?: string | null;
  error_message?: string | null;
}

export interface ResumeUploadBatchResponse {
  total: number;
  successful: number;
  failed: number;
  results: ResumeUploadResult[];
}

export interface ScoreComponent {
  score: number;
  max: number;
}

export interface ScoreBreakdown {
  skills: ScoreComponent;
  semantic: ScoreComponent;
  experience: ScoreComponent;
  education: ScoreComponent;
  relevance: ScoreComponent;
}

export interface JobMatchRankedItem {
  match_id: number;
  resume_id: number;
  filename: string;
  name?: string | null;
  email?: string | null;
  total_experience_years: number;
  overall_score: number;
  score_breakdown: ScoreBreakdown;
  matched_skills: string[];
  partially_matched_skills: string[];
  missing_skills: string[];
  rank: number;
  llm_score?: number | null;
  llm_analysis?: CandidateAiEvaluation | { error: string } | null;
}

export interface CandidateDetailedInfo {
  resume_id: number;
  filename: string;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  skills: string[];
  total_experience_years: number;
  companies_and_designations: CompanyRole[];
  education: EducationEntry[];
  certifications: string[];
  projects: ProjectEntry[];
}

export interface JobDetailedInfo {
  job_id: number;
  title: string;
  min_experience: number;
  required_skills: string[];
  core_skills: string[];
  preferred_skills: string[];
  education: string[];
}

export interface CandidateAiSummary {
  summary: string;
  strengths: string[];
  concerns: string[];
  recommendation: 'Strong fit' | 'Possible fit' | 'Weak fit';
}

export interface CandidateAiEvaluation {
  ai_score: number;
  matched_skills: string[];
  missing_skills: string[];
  equivalent_skills: string[];
  experience_assessment: string;
  summary: string;
  strengths: string[];
  concerns: string[];
  recommendation: 'Strong fit' | 'Possible fit' | 'Weak fit';
  reasons: string[];
  error?: string | null;
}

export type ScoringMode = 'standard' | 'ai';

export interface LlmStatus {
  enabled: boolean;
  max_candidates?: number;
}

export interface JobMatchDetailedResponse {
  match_id: number;
  overall_score: number;
  score_breakdown: ScoreBreakdown;
  matched_skills: string[];
  partially_matched_skills: string[];
  missing_skills: string[];
  reasons: string[];
  ai_summary?: CandidateAiSummary | null;
  llm_score?: number | null;
  llm_analysis?: CandidateAiEvaluation | null;
  created_at?: string;
  candidate: CandidateDetailedInfo;
  job: JobDetailedInfo;
}
