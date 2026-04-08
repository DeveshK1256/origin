import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Home", to: "/" },
  { label: "Features", to: "/features" },
  { label: "How It Works", to: "/how-it-works" },
  { label: "Contact", to: "/contact" }
];

export default function MarketingLayout({ children }) {
  return (
    <div className="min-h-screen bg-website text-ink">
      <header className="sticky top-0 z-40 border-b border-website-edge/80 bg-white/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 md:px-8">
          <NavLink to="/" className="group inline-flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-md bg-teal-700 font-display text-sm font-bold text-white">
              AR
            </span>
            <span className="font-display text-sm font-bold text-ink md:text-base">
              AI Recruitment Intelligence
            </span>
          </NavLink>

          <nav className="hidden items-center gap-1 md:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-semibold transition ${
                    isActive ? "bg-teal-700 text-white" : "text-slate-700 hover:bg-teal-50"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <NavLink
            to="/app/resume-scanner"
            className="rounded-lg bg-orange-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-orange-700 md:text-sm"
          >
            Open App
          </NavLink>
        </div>
      </header>

      <main>{children}</main>

      <footer className="border-t border-website-edge/80 bg-white/80">
        <div className="mx-auto grid w-full max-w-7xl gap-4 px-4 py-8 md:grid-cols-2 md:px-8">
          <div>
            <p className="font-display text-base font-bold text-ink">AI Recruitment Intelligence</p>
            <p className="mt-1 max-w-xl text-sm text-slate-600">
              Resume intelligence, matching, fraud screening, and AI-assisted resume building in one modern workspace.
            </p>
          </div>
          <div className="text-sm text-slate-600 md:text-right">
            <p>Built for recruiters, hiring teams, and job seekers.</p>
            <p className="mt-1">Use the app workspace for full functionality.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
