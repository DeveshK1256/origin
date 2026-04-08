import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Resume Scanner", to: "/resume-scanner" },
  { label: "Resume AI", to: "/resume-ai" },
  { label: "Job Analyzer", to: "/job-analyzer" },
  { label: "Fake Job Detection", to: "/fake-job-detection" }
];

function MetricPill({ label, value }) {
  return (
    <div className="rounded-xl border border-edge bg-white/80 px-3 py-2 text-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="font-display text-lg font-bold text-ink">{value ?? "--"}{value !== null ? "%" : ""}</p>
    </div>
  );
}

export default function AppLayout({ children, metrics }) {
  return (
    <div className="min-h-screen bg-mist text-ink">
      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 pb-8 pt-6 md:px-8">
        <header className="rounded-3xl border border-edge bg-gradient-to-r from-teal-100 via-white to-orange-100 p-6 shadow-lift">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">Recruitment Ops</p>
              <h1 className="font-display text-3xl font-bold text-ink">AI Recruitment Intelligence Platform</h1>
              <p className="mt-1 text-sm text-slate-600">
                Parse resumes, match roles, and detect high-risk job postings in one workflow.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <MetricPill label="Resume" value={metrics.resumeScore} />
              <MetricPill label="Match" value={metrics.jobMatch} />
              <MetricPill label="Scam Risk" value={metrics.scamRisk} />
            </div>
          </div>
        </header>

        <div className="grid gap-5 lg:grid-cols-[260px,1fr]">
          <aside className="rounded-2xl border border-edge bg-panel p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Navigation
            </p>
            <nav className="space-y-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `block rounded-xl px-3 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "bg-teal-700 text-white shadow"
                        : "bg-white text-slate-700 hover:bg-teal-50"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </aside>

          <main className="rounded-2xl border border-edge bg-panel p-4 md:p-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
