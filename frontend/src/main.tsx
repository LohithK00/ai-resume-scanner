import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Upload,
  FileText,
  Users,
  Target,
  Sparkles,
  CheckCircle2,
  BriefcaseBusiness,
  LogOut,
  LayoutDashboard,
  Search,
  BarChart3,
  ArrowLeft,
  Download,
  Clock3,
  UserRound,
  ShieldCheck,
  Maximize2,
  Minimize2,
  ExternalLink,
  AlertCircle,
  Mail,
  Phone,
  X,
} from 'lucide-react';
import './styles.css';

const API =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

type User = {
  id: number;
  name: string;
  email: string;
  role: 'candidate' | 'admin';
};

type Job = {
  id: number;
  title: string;
  description: string;
  required_skills: string[];
  created_at: string;
};

type Resume = {
  id: number;
  job_id: number;
  filename: string;
  name: string;
  email?: string;
  phone?: string;
  parsed_data: any;
  skill_score: number;
  semantic_score: number;
  experience_score: number;
  education_score: number;
  certification_score: number;
  final_score: number;
  recommendation: string;
};

type AppItem = {
  id: number;
  status: string;
  ai_suggestions: string[];
  applied_at: string;
  updated_at: string;
  job: Job;
  resume: Resume;
  candidate_name?: string;
  candidate_email?: string;
};

async function api(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('resume_token');

  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('X-User-Token', token);
  }

  const r = await fetch(`${API}${path}`, {
    ...options,
    headers,
  });

  const data = await r.json().catch(() => null);

  if (!r.ok) {
    throw new Error(data?.detail || 'Request failed');
  }

  return data;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] =
    useState<'login' | 'register'>('login');
  const [authRole, setAuthRole] =
    useState<'candidate' | 'admin'>('candidate');

  const [authName, setAuthName] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [view, setView] = useState('dashboard');

  useEffect(() => {
    const saved = localStorage.getItem('resume_user');

    if (saved) {
      setUser(JSON.parse(saved));
    }
  }, []);

  if (!user) {
    return (
      <Auth
        mode={authMode}
        setMode={setAuthMode}
        role={authRole}
        setRole={setAuthRole}
        name={authName}
        setName={setAuthName}
        email={authEmail}
        setEmail={setAuthEmail}
        password={authPassword}
        setPassword={setAuthPassword}
        error={authError}
        onSubmit={async () => {
          try {
            setAuthError('');

            const data = await api(
              authMode === 'login'
                ? '/auth/login'
                : '/auth/register',
              {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(
                  authMode === 'login'
                    ? {
                        email: authEmail,
                        password: authPassword,
                      }
                    : {
                        name: authName,
                        email: authEmail,
                        password: authPassword,
                        role: authRole,
                      }
                ),
              }
            );

            localStorage.setItem('resume_token', data.token);
            localStorage.setItem(
              'resume_user',
              JSON.stringify(data.user)
            );

            setUser(data.user);
          } catch (e: any) {
            setAuthError(e.message);
          }
        }}
      />
    );
  }

  const logout = () => {
    localStorage.removeItem('resume_token');
    localStorage.removeItem('resume_user');
    setUser(null);
  };

  return (
    <div className="app">
      <Sidebar
        user={user}
        view={view}
        setView={setView}
        logout={logout}
      />

      {user.role === 'admin' ? (
        <AdminPortal view={view} setView={setView} />
      ) : (
        <CandidatePortal view={view} setView={setView} />
      )}
    </div>
  );
}

function Auth(p: any) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand big">
          <Sparkles />
          <span>ResumeAI</span>
        </div>

        <div className="eyebrow">AI RECRUITMENT PLATFORM</div>

        <h1>
          {p.mode === 'login'
            ? 'Welcome back'
            : 'Create your account'}
        </h1>

        <p>
          {p.mode === 'login'
            ? 'Sign in to access your portal.'
            : 'Choose your portal and start using AI-powered resume screening.'}
        </p>

        {p.mode === 'register' && (
          <input
            placeholder="Full name"
            value={p.name}
            onChange={(e) => p.setName(e.target.value)}
          />
        )}

        <input
          placeholder="Email"
          type="email"
          value={p.email}
          onChange={(e) => p.setEmail(e.target.value)}
        />

        <input
          placeholder="Password (6+ characters)"
          type="password"
          value={p.password}
          onChange={(e) => p.setPassword(e.target.value)}
        />

        {p.mode === 'register' && (
          <div className="role-switch">
            <button
              className={
                p.role === 'candidate' ? 'selected' : ''
              }
              onClick={() => p.setRole('candidate')}
            >
              <UserRound />
              Candidate
            </button>

            <button
              className={
                p.role === 'admin' ? 'selected' : ''
              }
              onClick={() => p.setRole('admin')}
            >
              <ShieldCheck />
              Admin
            </button>
          </div>
        )}

        {p.error && <div className="error">{p.error}</div>}

        <button className="primary full" onClick={p.onSubmit}>
          {p.mode === 'login' ? 'Sign in' : 'Create account'}
        </button>

        <button
          className="link-btn"
          onClick={() =>
            p.setMode(
              p.mode === 'login' ? 'register' : 'login'
            )
          }
        >
          {p.mode === 'login'
            ? "Don't have an account? Register"
            : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  );
}

function Sidebar({
  user,
  view,
  setView,
  logout,
}: {
  user: User;
  view: string;
  setView: (v: string) => void;
  logout: () => void;
}) {
  const items =
    user.role === 'admin'
      ? [
          ['dashboard', 'Dashboard', LayoutDashboard],
          ['jobs', 'Jobs', BriefcaseBusiness],
          ['applicants', 'Applicants', Users],
          ['reports', 'Reports', BarChart3],
        ]
      : [
          ['dashboard', 'Find Jobs', Search],
          ['applications', 'My Applications', FileText],
          ['improvement', 'Resume Improvement', Sparkles],
        ];

  return (
    <aside>
      <div className="brand">
        <Sparkles />
        <span>ResumeAI</span>
      </div>

      <div className="portal-label">
        {user.role === 'admin'
          ? 'ADMIN PORTAL'
          : 'CANDIDATE PORTAL'}
      </div>

      <div className="user-box">
        <div className="avatar">
          {user.name.charAt(0).toUpperCase()}
        </div>

        <div>
          <strong>{user.name}</strong>
          <small>{user.email}</small>
        </div>
      </div>

      {items.map(([key, label, Icon]: any) => (
        <button
          key={key}
          className={`nav ${
            view === key ? 'active' : ''
          }`}
          onClick={() => setView(key)}
        >
          <Icon />
          {label}
        </button>
      ))}

      <button className="nav logout" onClick={logout}>
        <LogOut />
        Sign out
      </button>
    </aside>
  );
}

function AdminPortal({
  view,
  setView,
}: {
  view: string;
  setView: (v: string) => void;
}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [apps, setApps] = useState<AppItem[]>([]);
  const [stats, setStats] = useState<any>({});
  const [selected, setSelected] =
    useState<AppItem | null>(null);
  const [title, setTitle] = useState(
    'Machine Learning Engineer'
  );
  const [description, setDescription] = useState(
    'We are looking for a Machine Learning Engineer with 2 years experience in Python, machine learning, TensorFlow, SQL and Flask. A bachelor degree is preferred. Docker and AWS are desirable.'
  );
  const [msg, setMsg] = useState('');

  const load = async () => {
    try {
      setJobs(await api('/admin/jobs'));
      setApps(await api('/admin/applications'));
      setStats(await api('/admin/stats'));
    } catch (e: any) {
      setMsg(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const create = async () => {
    try {
      const j = await api('/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          description,
        }),
      });

      setJobs((x) => [j, ...x]);
      setMsg(
        'Job published. Candidates can now apply immediately.'
      );
    } catch (e: any) {
      setMsg(e.message);
    }
  };

  const status = async (id: number, s: string) => {
    try {
      await api(`/admin/applications/${id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: s }),
      });

      await load();

      if (selected) {
        setSelected({
          ...selected,
          status: s,
        });
      }
    } catch (e: any) {
      setMsg(e.message);
    }
  };

  if (selected) {
    return (
      <main>
        <button
          className="back"
          onClick={() => setSelected(null)}
        >
          <ArrowLeft />
          Back to applicants
        </button>

        <CandidateAdminDetail
          item={selected}
          updateStatus={status}
        />
      </main>
    );
  }

  return (
    <main>
      <header>
        <div>
          <div className="eyebrow">ADMIN PORTAL</div>

          <h1>
            {view === 'dashboard'
              ? 'Recruitment Dashboard'
              : view === 'jobs'
              ? 'Job Management'
              : view === 'applicants'
              ? 'Candidate Screening'
              : 'Reports & Analytics'}
          </h1>

          <p>
            Post jobs, receive applications and review
            AI-analyzed candidates automatically.
          </p>
        </div>
      </header>

      {msg && <div className="message">{msg}</div>}

      {view === 'dashboard' && (
        <>
          <Stats stats={stats} />

          <section className="panel">
            <div className="section-head">
              <div>
                <h2>Recent applications</h2>
                <p>
                  Every candidate application is automatically
                  analyzed at upload time.
                </p>
              </div>

              <button
                className="secondary"
                onClick={() => setView('applicants')}
              >
                View all
              </button>
            </div>

            <ApplicantTable
              apps={apps.slice(0, 5)}
              onSelect={setSelected}
            />
          </section>
        </>
      )}

      {view === 'jobs' && (
        <>
          <section className="grid">
            <div className="panel">
              <h2>Post a new job</h2>

              <label>Job title</label>

              <input
                value={title}
                onChange={(e) =>
                  setTitle(e.target.value)
                }
              />

              <label>Job description</label>

              <textarea
                rows={9}
                value={description}
                onChange={(e) =>
                  setDescription(e.target.value)
                }
              />

              <button
                className="primary"
                onClick={create}
              >
                Publish Job
              </button>
            </div>

            <section className="panel">
              <h2>Published jobs</h2>

              {jobs.map((j) => (
                <div className="job-card" key={j.id}>
                  <div>
                    <strong>{j.title}</strong>

                    <small>
                      {j.required_skills.join(' • ')}
                    </small>
                  </div>

                  <span>
                    {
                      apps.filter(
                        (a) => a.job.id === j.id
                      ).length
                    }{' '}
                    applicants
                  </span>
                </div>
              ))}
            </section>
          </section>
        </>
      )}

      {view === 'applicants' && (
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>All candidates</h2>

              <p>
                ATS score, skill match, semantic match and AI
                recommendations.
              </p>
            </div>
          </div>

          <ApplicantTable
            apps={apps}
            onSelect={setSelected}
            admin
          />
        </section>
      )}

      {view === 'reports' && (
        <Reports apps={apps} stats={stats} />
      )}
    </main>
  );
}

function CandidatePortal({
  view,
  setView,
}: {
  view: string;
  setView: (v: string) => void;
}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [apps, setApps] = useState<AppItem[]>([]);
  const [selected, setSelected] =
    useState<AppItem | null>(null);
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      setJobs(await api('/candidate/jobs'));
      setApps(await api('/candidate/applications'));
    } catch (e: any) {
      setMsg(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const apply = async (job: Job, file: File) => {
    setLoading(true);

    try {
      const fd = new FormData();
      fd.append('file', file);

      await api(`/candidate/jobs/${job.id}/apply`, {
        method: 'POST',
        body: fd,
      });

      setMsg(
        `Application submitted for ${job.title}. Your resume was analyzed automatically.`
      );

      await load();
      setView('applications');
    } catch (e: any) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (selected) {
    return (
      <main>
        <button
          className="back"
          onClick={() => setSelected(null)}
        >
          <ArrowLeft />
          Back to applications
        </button>

        <CandidateDetail item={selected} />
      </main>
    );
  }

  return (
    <main>
      <header>
        <div>
          <div className="eyebrow">CANDIDATE PORTAL</div>

          <h1>
            {view === 'dashboard'
              ? 'Find your next opportunity'
              : view === 'applications'
              ? 'My Applications'
              : 'Resume Improvement'}
          </h1>

          <p>
            Apply once and let AI analyze your resume against
            the job requirements automatically.
          </p>
        </div>
      </header>

      {msg && <div className="message">{msg}</div>}

      {view === 'dashboard' && (
        <section className="job-grid">
          {jobs.map((j) => (
            <JobCard
              key={j.id}
              job={j}
              onApply={apply}
              loading={loading}
            />
          ))}
        </section>
      )}

      {view === 'applications' && (
        <section className="panel">
          <h2>Application status</h2>

          {apps.length ? (
            <div className="application-list">
              {apps.map((a) => (
                <button
                  className="application-card"
                  key={a.id}
                  onClick={() => setSelected(a)}
                >
                  <div>
                    <strong>{a.job.title}</strong>

                    <small>
                      Applied{' '}
                      {new Date(
                        a.applied_at
                      ).toLocaleDateString()}
                    </small>
                  </div>

                  <div>
                    <span
                      className={`status ${a.status
                        .toLowerCase()
                        .replaceAll(' ', '-')}`}
                    >
                      {a.status}
                    </span>

                    <b>
                      {a.resume.final_score.toFixed(1)}% ATS
                    </b>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <Empty text="You have not applied for any jobs yet." />
          )}
        </section>
      )}

      {view === 'improvement' && (
        <Improvement
          apps={apps}
          onSelect={setSelected}
        />
      )}
    </main>
  );
}

function JobCard({
  job,
  onApply,
  loading,
}: {
  job: Job;
  onApply: (j: Job, f: File) => void;
  loading: boolean;
}) {
  const [file, setFile] =
    useState<File | null>(null);

  return (
    <div className="panel job-card-large">
      <div className="job-icon">
        <BriefcaseBusiness />
      </div>

      <h2>{job.title}</h2>

      <p>{job.description}</p>

      <div>
        {job.required_skills.map((s) => (
          <span className="chip" key={s}>
            {s}
          </span>
        ))}
      </div>

      <label className="drop compact">
        <Upload size={26} />

        <strong>
          {file ? file.name : 'Upload your resume'}
        </strong>

        <span>PDF / DOCX</span>

        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) =>
            setFile(
              e.target.files?.[0] || null
            )
          }
        />
      </label>

      <button
        className="primary full"
        disabled={!file || loading}
        onClick={() =>
          file && onApply(job, file)
        }
      >
        {loading
          ? 'AI analyzing…'
          : 'Apply & Analyze Resume'}
      </button>
    </div>
  );
}

function CandidateDetail({
  item,
}: {
  item: AppItem;
}) {
  const r = item.resume;

  return (
    <>
      <section className="panel hero-detail">
        <div>
          <div className="eyebrow">
            APPLICATION #{item.id}
          </div>

          <h1>{item.job.title}</h1>

          <span
            className={`status ${item.status
              .toLowerCase()
              .replaceAll(' ', '-')}`}
          >
            {item.status}
          </span>
        </div>

        <div className="ats-big">
          {r.final_score.toFixed(1)}
          <small>ATS MATCH</small>
        </div>
      </section>

      <section className="metric-grid">
        <Metric label="Skill Match" value={r.skill_score} />
        <Metric
          label="Semantic Match"
          value={r.semantic_score}
        />
        <Metric
          label="Experience"
          value={r.experience_score}
        />
        <Metric
          label="Education"
          value={r.education_score}
        />
        <Metric
          label="Certifications"
          value={r.certification_score}
        />
      </section>

      <section className="grid">
        <section className="panel">
          <h2>AI analysis</h2>

          <h3>Matched skills</h3>

          {(r.parsed_data.matched_skills || []).map(
            (s: string) => (
              <span
                className="chip good"
                key={s}
              >
                {s}
              </span>
            )
          )}

          <h3 className="mt">Missing skills</h3>

          {(r.parsed_data.missing_skills || []).map(
            (s: string) => (
              <span
                className="chip missing"
                key={s}
              >
                {s}
              </span>
            )
          )}
        </section>

        <section className="panel">
          <h2>AI improvement suggestions</h2>

          {item.ai_suggestions.map(
            (s, i) => (
              <div
                className="suggestion"
                key={i}
              >
                <Sparkles />
                <span>{s}</span>
              </div>
            )
          )}
        </section>
      </section>
    </>
  );
}

/* =========================================================
   PROFESSIONAL ADMIN CANDIDATE WORKSPACE
   ========================================================= */

function CandidateAdminDetail({
  item,
  updateStatus,
}: {
  item: AppItem;
  updateStatus: (id: number, s: string) => void;
}) {
  const [resumeUrl, setResumeUrl] =
    useState<string | null>(null);

  const [resumeLoading, setResumeLoading] =
    useState(true);

  const [resumeError, setResumeError] =
    useState('');

  const [fullscreen, setFullscreen] =
    useState(false);

  const [downloadUrl, setDownloadUrl] =
    useState<string | null>(null);

  const r = item.resume;

  const candidateName =
    item.candidate_name ||
    r.name ||
    'Unknown Candidate';

  const candidateEmail =
    item.candidate_email ||
    r.email ||
    'No email available';

  const initials = candidateName
    .split(' ')
    .filter(Boolean)
    .map((x) => x[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const extension =
    r.filename?.split('.').pop()?.toLowerCase() || '';

  const isPdf = extension === 'pdf';

  useEffect(() => {
    let objectUrl: string | null = null;

    const loadResume = async () => {
      setResumeLoading(true);
      setResumeError('');

      try {
        const token =
          localStorage.getItem('resume_token');

        const response = await fetch(
          `${API}/admin/resumes/${r.id}/file`,
          {
            headers: {
              'X-User-Token': token || '',
            },
          }
        );

        if (!response.ok) {
          const data =
            await response
              .json()
              .catch(() => null);

          throw new Error(
            data?.detail ||
              'Unable to load the original resume.'
          );
        }

        const blob = await response.blob();

        objectUrl = URL.createObjectURL(blob);

        setResumeUrl(objectUrl);
        setDownloadUrl(objectUrl);
      } catch (error: any) {
        setResumeError(
          error?.message ||
            'Unable to load the resume.'
        );
      } finally {
        setResumeLoading(false);
      }
    };

    loadResume();

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [r.id]);

  useEffect(() => {
    if (!fullscreen) {
      document.body.style.overflow = '';
      return;
    }

    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = '';
    };
  }, [fullscreen]);

  const downloadResume = () => {
    if (!downloadUrl) return;

    const a =
      document.createElement('a');

    a.href = downloadUrl;
    a.download =
      r.filename || `resume-${r.id}.${extension}`;

    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const openResume = () => {
    if (!resumeUrl) return;

    window.open(
      resumeUrl,
      '_blank',
      'noopener,noreferrer'
    );
  };

  return (
    <div className="candidate-admin-workspace">
      {/* Candidate Header */}
      <section className="candidate-workspace-header">
        <div>
          <div className="eyebrow">
            AI CANDIDATE ANALYSIS
          </div>

          <div className="candidate-title-row">
            <div className="candidate-avatar-large">
              {initials}
            </div>

            <div>
              <h1>{candidateName}</h1>

              <div className="candidate-meta">
                <span>
                  <Mail size={13} />{' '}
                  {candidateEmail}
                </span>

                <span>•</span>

                <span>
                  {item.job.title}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="workspace-actions">
          <span
            className={`status ${item.status
              .toLowerCase()
              .replaceAll(' ', '-')}`}
          >
            {item.status}
          </span>

          <div className="status-actions compact-actions">
            {[
              'UNDER REVIEW',
              'SHORTLISTED',
              'INTERVIEW',
              'REJECTED',
              'HIRED',
            ].map((s) => (
              <button
                className={
                  item.status === s
                    ? 'selected-status'
                    : ''
                }
                key={s}
                onClick={() =>
                  updateStatus(item.id, s)
                }
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Main Workspace */}
      <section className="workspace-grid">
        {/* LEFT - Candidate Intelligence */}
        <div className="candidate-intelligence">
          {/* ATS Summary */}
          <section className="panel ats-summary-card">
            <div className="ats-summary-top">
              <div>
                <div className="eyebrow">
                  ATS INTELLIGENCE
                </div>

                <h2>
                  Candidate match analysis
                </h2>
              </div>

              <div className="ats-score-circle">
                <strong>
                  {r.final_score.toFixed(0)}
                </strong>

                <span>ATS SCORE</span>
              </div>
            </div>

            <div className="recommendation-box">
              <span>
                AI recommendation
              </span>

              <strong>
                {r.recommendation}
              </strong>
            </div>
          </section>

          {/* Match Breakdown */}
          <section className="panel">
            <h2>Match breakdown</h2>

            <div className="metric-grid recruiter-metrics">
              <Metric
                label="Skill Match"
                value={r.skill_score}
              />

              <Metric
                label="Semantic Match"
                value={r.semantic_score}
              />

              <Metric
                label="Experience"
                value={r.experience_score}
              />

              <Metric
                label="Education"
                value={r.education_score}
              />

              <Metric
                label="Certification"
                value={r.certification_score}
              />
            </div>
          </section>

          {/* Candidate Information */}
          <section className="panel">
            <h2>Candidate information</h2>

            <div className="info-grid">
              <Info
                label="Full name"
                value={candidateName}
              />

              <Info
                label="Email"
                value={candidateEmail}
              />

              <Info
                label="Phone"
                value={r.phone || '—'}
              />

              <Info
                label="Applied for"
                value={item.job.title}
              />

              <Info
                label="Application date"
                value={new Date(
                  item.applied_at
                ).toLocaleDateString()}
              />

              <Info
                label="Resume"
                value={r.filename}
              />
            </div>
          </section>

          {/* Skills */}
          <section className="panel">
            <h2>Skills intelligence</h2>

            <h3 className="skill-heading matched-heading">
              Matched skills
            </h3>

            <div className="chip-wrap">
              {(r.parsed_data?.matched_skills ||
                []).map((s: string) => (
                <span
                  className="chip good"
                  key={s}
                >
                  {s}
                </span>
              ))}

              {!(
                r.parsed_data?.matched_skills ||
                []
              ).length && (
                <span className="candidate-muted">
                  No matched skills detected.
                </span>
              )}
            </div>

            <h3 className="skill-heading missing-heading">
              Missing skills
            </h3>

            <div className="chip-wrap">
              {(r.parsed_data?.missing_skills ||
                []).map((s: string) => (
                <span
                  className="chip missing"
                  key={s}
                >
                  {s}
                </span>
              ))}

              {!(
                r.parsed_data?.missing_skills ||
                []
              ).length && (
                <span className="candidate-muted">
                  No major missing skills detected.
                </span>
              )}
            </div>
          </section>

          {/* AI Assessment */}
          <section className="panel">
            <h2>AI assessment</h2>

            <div className="ai-assessment">
              <Sparkles />

              <div>
                <strong>
                  Automated screening assessment
                </strong>

                <p>
                  The candidate's resume was
                  automatically evaluated against
                  the requirements of{' '}
                  <b>{item.job.title}</b>.
                  The ATS score combines skills,
                  semantic relevance, experience,
                  education and certification
                  signals.
                </p>
              </div>
            </div>
          </section>

          {/* AI Suggestions */}
          <section className="panel">
            <h2>
              AI suggestions shown to candidate
            </h2>

            {item.ai_suggestions.length ? (
              item.ai_suggestions.map(
                (s, i) => (
                  <div
                    className="suggestion"
                    key={i}
                  >
                    <Sparkles />

                    <span>{s}</span>
                  </div>
                )
              )
            ) : (
              <div className="candidate-muted">
                No AI suggestions available.
              </div>
            )}
          </section>
        </div>

        {/* RIGHT - Resume Viewer */}
        <section
          className={`panel resume-viewer-panel ${
            fullscreen
              ? 'resume-fullscreen'
              : ''
          }`}
        >
          <div className="resume-viewer-header">
            <div>
              <div className="eyebrow">
                RESUME
              </div>

              <h2 title={r.filename}>
                {r.filename}
              </h2>
            </div>

            <div className="resume-viewer-actions">
              <button
                className="icon-action"
                title="Open resume in new tab"
                onClick={openResume}
                disabled={!resumeUrl}
              >
                <ExternalLink size={17} />
              </button>

              <button
                className="icon-action"
                title="Download resume"
                onClick={downloadResume}
                disabled={!downloadUrl}
              >
                <Download size={17} />
              </button>

              <button
                className="icon-action"
                title={
                  fullscreen
                    ? 'Exit fullscreen'
                    : 'Fullscreen'
                }
                onClick={() =>
                  setFullscreen(!fullscreen)
                }
              >
                {fullscreen ? (
                  <Minimize2 size={17} />
                ) : (
                  <Maximize2 size={17} />
                )}
              </button>

              {fullscreen && (
                <button
                  className="icon-action"
                  title="Close"
                  onClick={() =>
                    setFullscreen(false)
                  }
                >
                  <X size={17} />
                </button>
              )}
            </div>
          </div>

          <div className="resume-viewer">
            {resumeLoading && (
              <div className="resume-empty-state">
                <FileText size={40} />

                <strong>
                  Loading resume...
                </strong>

                <span>
                  Securely retrieving the original
                  candidate document.
                </span>
              </div>
            )}

            {!resumeLoading && resumeError && (
              <div className="resume-empty-state error-state">
                <AlertCircle size={42} />

                <strong>
                  Resume unavailable
                </strong>

                <span>
                  {resumeError}
                </span>

                <button
                  className="secondary"
                  onClick={openResume}
                  disabled={!resumeUrl}
                >
                  Open resume
                </button>
              </div>
            )}

            {!resumeLoading &&
              !resumeError &&
              resumeUrl &&
              isPdf && (
                <iframe
                  className="resume-frame"
                  src={resumeUrl}
                  title={`${candidateName} resume`}
                />
              )}

            {!resumeLoading &&
              !resumeError &&
              resumeUrl &&
              !isPdf && (
                <div className="resume-empty-state">
                  <FileText size={42} />

                  <strong>
                    DOCX resume
                  </strong>

                  <span>
                    Browser preview is not available
                    for this Word document. Use
                    Download or Open to view the
                    original file.
                  </span>

                  <div
                    className="resume-viewer-actions"
                  >
                    <button
                      className="secondary"
                      onClick={downloadResume}
                    >
                      <Download size={15} />
                      Download DOCX
                    </button>

                    <button
                      className="secondary"
                      onClick={openResume}
                    >
                      <ExternalLink size={15} />
                      Open file
                    </button>
                  </div>
                </div>
              )}
          </div>
        </section>
      </section>
    </div>
  );
}

function Improvement({
  apps,
  onSelect,
}: {
  apps: AppItem[];
  onSelect: (a: AppItem) => void;
}) {
  return (
    <section className="grid">
      <section className="panel">
        <h2>Resume improvement center</h2>

        <p>
          AI suggestions are generated immediately
          after each application.
        </p>

        {apps.map((a) => (
          <div
            className="improve-card"
            key={a.id}
          >
            <div>
              <strong>{a.job.title}</strong>

              <small>
                ATS{' '}
                {a.resume.final_score.toFixed(1)}%
              </small>
            </div>

            <button
              className="secondary"
              onClick={() => onSelect(a)}
            >
              View suggestions
            </button>
          </div>
        ))}

        {!apps.length && (
          <Empty text="Apply for a job to receive personalized AI feedback." />
        )}
      </section>

      <section className="panel">
        <h2>What the AI checks</h2>

        {[
          'Required skills and missing skills',
          'Resume-to-job semantic similarity',
          'Relevant experience',
          'Education alignment',
          'Certifications',
          'ATS-style overall match',
          'Actionable resume improvement suggestions',
        ].map((x) => (
          <div
            className="check-line"
            key={x}
          >
            <CheckCircle2 />
            {x}
          </div>
        ))}
      </section>
    </section>
  );
}

function ApplicantTable({
  apps,
  onSelect,
  admin = false,
}: {
  apps: AppItem[];
  onSelect: (a: AppItem) => void;
  admin?: boolean;
}) {
  return (
    <div className="table">
      <div className="tr th">
        <span>#</span>
        <span>Candidate</span>
        <span>Job</span>
        <span>Skills</span>
        <span>ATS</span>
        <span>Status</span>
      </div>

      {apps.map((a, i) => (
        <button
          className="tr row-button"
          key={a.id}
          onClick={() => onSelect(a)}
        >
          <span>{i + 1}</span>

          <span>
            <strong>
              {a.candidate_name ||
                a.resume.name}
            </strong>

            <small>
              {a.candidate_email ||
                a.resume.email ||
                a.resume.filename}
            </small>
          </span>

          <span>{a.job.title}</span>

          <span>
            {a.resume.skill_score.toFixed(0)}%
          </span>

          <span className="score">
            {a.resume.final_score.toFixed(1)}%
          </span>

          <span>
            <b
              className={`badge ${a.resume.recommendation
                .toLowerCase()
                .replaceAll(' ', '-')}`}
            >
              {admin
                ? a.status
                : a.resume.recommendation}
            </b>
          </span>
        </button>
      ))}

      {!apps.length && (
        <Empty text="No candidate applications yet." />
      )}
    </div>
  );
}

function Stats({
  stats,
}: {
  stats: any;
}) {
  return (
    <section className="stats big-stats">
      <Stat
        icon={<BriefcaseBusiness />}
        value={stats.jobs || 0}
        label="Jobs"
      />

      <Stat
        icon={<Users />}
        value={stats.applications || 0}
        label="Applications"
      />

      <Stat
        icon={<CheckCircle2 />}
        value={stats.shortlisted || 0}
        label="Shortlisted"
      />

      <Stat
        icon={<Sparkles />}
        value={stats.strong_matches || 0}
        label="Strong AI matches"
      />

      <Stat
        icon={<Target />}
        value={stats.average_score || 0}
        label="Average ATS"
      />
    </section>
  );
}

function Reports({
  apps,
  stats,
}: {
  apps: AppItem[];
  stats: any;
}) {
  const download = async () => {
    const token =
      localStorage.getItem('resume_token');

    const r = await fetch(
      `${API}/admin/reports.csv`,
      {
        headers: {
          'X-User-Token': token || '',
        },
      }
    );

    const blob = await r.blob();
    const url =
      URL.createObjectURL(blob);

    const a =
      document.createElement('a');

    a.href = url;
    a.download =
      'resume_screening_report.csv';

    a.click();

    URL.revokeObjectURL(url);
  };

  const dist = useMemo(
    () => ({
      strong: apps.filter(
        (a) => a.resume.final_score >= 85
      ).length,

      short: apps.filter(
        (a) =>
          a.resume.final_score >= 75 &&
          a.resume.final_score < 85
      ).length,

      review: apps.filter(
        (a) =>
          a.resume.final_score >= 60 &&
          a.resume.final_score < 75
      ).length,

      low: apps.filter(
        (a) => a.resume.final_score < 60
      ).length,
    }),
    [apps]
  );

  return (
    <>
      <section className="stats big-stats">
        <Stat
          icon={<Target />}
          value={stats.average_score || 0}
          label="Average ATS"
        />

        <Stat
          icon={<Sparkles />}
          value={dist.strong}
          label="Strong matches"
        />

        <Stat
          icon={<CheckCircle2 />}
          value={dist.short}
          label="Shortlist range"
        />

        <Stat
          icon={<Clock3 />}
          value={dist.review}
          label="Review"
        />
      </section>

      <section className="grid">
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Decision distribution</h2>

              <p>
                Current AI ranking across
                applications.
              </p>
            </div>

            <button
              className="secondary"
              onClick={download}
            >
              <Download />
              CSV
            </button>
          </div>

          {[
            ['Strong Match', dist.strong],
            ['Shortlist', dist.short],
            ['Review', dist.review],
            ['Low Match', dist.low],
          ].map(([name, n]: any) => (
            <div
              className="bar-row"
              key={name}
            >
              <span>{name}</span>

              <div>
                <i
                  style={{
                    width: `${
                      apps.length
                        ? (n / apps.length) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>

              <b>{n}</b>
            </div>
          ))}
        </section>

        <section className="panel">
          <h2>Top candidates</h2>

          {[
            ...apps,
          ]
            .sort(
              (a, b) =>
                b.resume.final_score -
                a.resume.final_score
            )
            .slice(0, 5)
            .map((a) => (
              <button
                className="top-row"
                key={a.id}
              >
                <span>
                  {a.candidate_name}
                </span>

                <b>
                  {a.resume.final_score.toFixed(
                    1
                  )}
                  %
                </b>
              </button>
            ))}
        </section>
      </section>
    </>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="metric">
      <span>{label}</span>

      <strong>
        {value.toFixed(0)}%
      </strong>

      <div>
        <i
          style={{
            width: `${Math.max(
              0,
              Math.min(100, value)
            )}%`,
          }}
        />
      </div>
    </div>
  );
}

function Info({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="info">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Stat({
  icon,
  value,
  label,
}: {
  icon: any;
  value: number | string;
  label: string;
}) {
  return (
    <div className="stat">
      <span className="stat-icon">
        {icon}
      </span>

      <strong>{value}</strong>

      <span>{label}</span>
    </div>
  );
}

function Empty({
  text,
}: {
  text: string;
}) {
  return (
    <div className="empty">
      <AlertTriangleIcon />
      {text}
    </div>
  );
}

function AlertTriangleIcon() {
  return (
    <span className="empty-icon">
      △
    </span>
  );
}

createRoot(
  document.getElementById('root')!
).render(<App />);