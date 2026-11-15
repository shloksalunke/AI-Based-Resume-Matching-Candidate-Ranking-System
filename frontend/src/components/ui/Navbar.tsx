import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, Briefcase, PlusCircle, Cpu } from 'lucide-react';
import { Badge } from './Badge';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-100 group-hover:scale-105 transition-transform">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-slate-900 text-base leading-tight tracking-tight">
                  ResumeMatcher <span className="text-indigo-600">AI</span>
                </span>
                <span className="text-[10px] text-slate-500 font-medium">Explainable Candidate Ranking</span>
              </div>
            </Link>

            <nav className="hidden md:flex items-center gap-1">
              <Link
                to="/"
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/') && location.pathname === '/'
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Briefcase className="w-4 h-4" />
                Jobs Dashboard
              </Link>
              <Link
                to="/jobs/new"
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/jobs/new')
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <PlusCircle className="w-4 h-4" />
                New Job
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant="success" size="sm" className="hidden sm:inline-flex items-center gap-1">
              <Cpu className="w-3 h-3" />
              100% Offline AI / spaCy
            </Badge>
          </div>
        </div>
      </div>
    </header>
  );
};
