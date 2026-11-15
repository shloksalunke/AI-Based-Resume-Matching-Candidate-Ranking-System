import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Upload, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';
import { useCreateJob } from '../hooks/useJobs';
import { Button, Card, Badge, SkillChip, FileDropzone } from '../components/ui';
import type { JobDescription } from '../types';

export const CreateJob: React.FC = () => {
  const navigate = useNavigate();
  const createJobMutation = useCreateJob();

  const [activeTab, setActiveTab] = useState<'text' | 'file'>('text');
  const [title, setTitle] = useState('');
  const [rawText, setRawText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [createdJob, setCreatedJob] = useState<JobDescription | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      alert('Please provide a job title');
      return;
    }

    const formData = new FormData();
    formData.append('title', title.trim());

    if (activeTab === 'text') {
      if (!rawText.trim() || rawText.trim().length < 10) {
        alert('Please paste a job description of at least 10 characters');
        return;
      }
      formData.append('raw_text', rawText.trim());
    } else {
      if (!selectedFile) {
        alert('Please select a file to upload');
        return;
      }
      formData.append('file', selectedFile);
    }

    createJobMutation.mutate(formData, {
      onSuccess: (data) => {
        setCreatedJob(data);
      },
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Create Job Description
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Our offline NLP engine will automatically extract required skills, core weights, minimum experience, and qualifications.
        </p>
      </div>

      {createdJob ? (
        <Card className="border-emerald-200 bg-emerald-50/20">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Job Description Parsed Successfully!</h2>
              <p className="text-sm text-slate-500">
                Extracted structure and weighted requirements are ready.
              </p>
            </div>
          </div>

          <div className="space-y-6 bg-white p-6 rounded-xl border border-slate-200/80 mb-6">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Role Title
              </span>
              <h3 className="text-lg font-bold text-slate-900">{createdJob.title}</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-xs font-semibold text-slate-500 block mb-1">Experience Requirement</span>
                <span className="text-sm font-bold text-slate-800">
                  {createdJob.min_experience > 0 ? `${createdJob.min_experience}+ Years` : 'Not explicitly required'}
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-xs font-semibold text-slate-500 block mb-1">Education Requirements</span>
                <span className="text-sm font-bold text-slate-800">
                  {createdJob.education && createdJob.education.length > 0
                    ? createdJob.education.join(', ')
                    : 'Any higher education'}
                </span>
              </div>
            </div>

            {createdJob.core_skills && createdJob.core_skills.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-slate-500 block mb-2">
                  Core Skills (3x Weight + Gated Requirement):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {createdJob.core_skills.map((s) => (
                    <Badge key={s} variant="purple">
                      ⭐ {s}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div>
              <span className="text-xs font-semibold text-slate-500 block mb-2">
                Required Skills ({createdJob.required_skills?.length || 0}):
              </span>
              <div className="flex flex-wrap gap-1.5">
                {createdJob.required_skills?.map((s) => (
                  <SkillChip key={s} name={s} status="default" />
                ))}
              </div>
            </div>

            {createdJob.preferred_skills && createdJob.preferred_skills.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-slate-500 block mb-2">
                  Preferred / Nice to Have Skills ({createdJob.preferred_skills.length}):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {createdJob.preferred_skills.map((s) => (
                    <SkillChip key={s} name={s} status="default" />
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setCreatedJob(null);
                setTitle('');
                setRawText('');
                setSelectedFile(null);
              }}
            >
              Create Another Job
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate(`/jobs/${createdJob.id}`)}
              icon={<ArrowRight className="w-4 h-4" />}
            >
              Upload Resumes for this Job
            </Button>
          </div>
        </Card>
      ) : (
        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Job Title <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Senior Java Spring Boot Developer"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Job Description Input Method
              </label>
              <div className="flex border-b border-slate-200 gap-6">
                <button
                  type="button"
                  onClick={() => setActiveTab('text')}
                  className={`pb-3 text-sm font-semibold flex items-center gap-2 transition-colors border-b-2 ${
                    activeTab === 'text'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  Paste Text
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('file')}
                  className={`pb-3 text-sm font-semibold flex items-center gap-2 transition-colors border-b-2 ${
                    activeTab === 'file'
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  Upload Document (PDF / DOCX / TXT)
                </button>
              </div>
            </div>

            {activeTab === 'text' ? (
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1.5">
                  Paste Full Job Description Text
                </label>
                <textarea
                  rows={10}
                  placeholder="Paste the job description here, including requirements, responsibilities, and qualifications..."
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  className="w-full p-3.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-mono"
                />
              </div>
            ) : (
              <div>
                <FileDropzone
                  multiple={false}
                  acceptedExtensions={['.pdf', '.docx', '.txt']}
                  onFilesSelected={(files) => setSelectedFile(files[0] || null)}
                />
              </div>
            )}

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <Button type="button" variant="ghost" onClick={() => navigate('/')}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                isLoading={createJobMutation.isPending}
                icon={<Sparkles className="w-4 h-4" />}
              >
                Parse & Save Job Description
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
};
