import { Link } from "react-router-dom";
import MarketingLayout from "../components/MarketingLayout";

export default function ContactPage() {
  return (
    <MarketingLayout>
      <section className="mx-auto w-full max-w-7xl px-4 pb-20 pt-14 md:px-8 md:pt-16">
        <div className="grid gap-5 md:grid-cols-[1fr,1fr]">
          <div className="rounded-2xl border border-website-edge bg-white p-6 shadow-soft">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal-700">Contact</p>
            <h1 className="mt-2 font-display text-4xl font-extrabold text-ink">Let's make hiring smarter.</h1>
            <p className="mt-3 text-sm text-slate-600">
              If you want to productionize this for your team, integrate with ATS, or customize scoring models, we can extend this platform.
            </p>
            <div className="mt-4 space-y-2 text-sm text-slate-700">
              <p>Email: support@ai-recruitment-intelligence.local</p>
              <p>Response time: within 1 business day</p>
              <p>Focus: recruiting teams, staffing agencies, and job portals</p>
            </div>
          </div>

          <div className="rounded-2xl border border-website-edge bg-gradient-to-br from-teal-100 via-white to-orange-100 p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-600">Next Action</p>
            <p className="mt-2 font-display text-2xl font-bold text-ink">Try the platform workflow now</p>
            <p className="mt-2 text-sm text-slate-700">
              Start with Resume AI for tailored resume generation, then run matching and fake-job checks.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                to="/app/resume-ai"
                className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800"
              >
                Open Resume AI
              </Link>
              <Link
                to="/app/fake-job-detection"
                className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-900"
              >
                Open Fake Job Detection
              </Link>
            </div>
          </div>
        </div>
      </section>
    </MarketingLayout>
  );
}
