import { Link } from "react-router-dom";
import MarketingLayout from "../components/MarketingLayout";

const phases = [
  {
    phase: "Phase 1",
    title: "Intake Candidate Context",
    description:
      "Ingest resumes with Resume Scanner or generate candidate-ready resumes in Resume AI for specific roles.",
    output: "Structured profile with skills, experience, and domain signals."
  },
  {
    phase: "Phase 2",
    title: "Align Against Target Role",
    description:
      "Paste target job description and produce match scoring, required overlap, critical gaps, and tailored recommendations.",
    output: "Actionable fit score and role-specific optimization plan."
  },
  {
    phase: "Phase 3",
    title: "Protect Candidates And Pipeline",
    description:
      "Run fake-job detection before outreach or application to reduce scam exposure and improve trust.",
    output: "Scam probability, risk level, and explanation drivers."
  }
];

export default function HowItWorksPage() {
  return (
    <MarketingLayout>
      <section className="mx-auto w-full max-w-7xl px-4 pb-20 pt-14 md:px-8 md:pt-16">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal-700">How It Works</p>
          <h1 className="mt-2 font-display text-4xl font-extrabold text-ink md:text-5xl">
            Built for real recruiting workflows.
          </h1>
          <p className="mt-3 text-base text-slate-600">
            Move from candidate intake to role-fit and risk checks through one coherent sequence.
          </p>
        </div>

        <div className="mt-8 space-y-4">
          {phases.map((item) => (
            <article key={item.phase} className="rounded-2xl border border-website-edge bg-white p-5 shadow-soft">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-orange-700">{item.phase}</p>
              <p className="mt-1 font-display text-2xl font-bold text-ink">{item.title}</p>
              <p className="mt-2 text-sm text-slate-700">{item.description}</p>
              <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-800">
                Output: {item.output}
              </p>
            </article>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap gap-2">
          <Link
            to="/app/resume-ai"
            className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800"
          >
            Start With Resume AI
          </Link>
          <Link
            to="/app/job-analyzer"
            className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-900"
          >
            Jump To Job Analyzer
          </Link>
        </div>
      </section>
    </MarketingLayout>
  );
}
