import { Link } from "react-router-dom";
import MarketingLayout from "../components/MarketingLayout";

const featureCards = [
  {
    title: "Resume Intelligence",
    description: "Parse resumes into structured hiring signals with skills, experience confidence, and domain fit."
  },
  {
    title: "Resume AI Builder",
    description: "Create a targeted resume from scratch or existing resume and generate downloadable LaTeX instantly."
  },
  {
    title: "Role Matching",
    description: "Match candidate profiles with target job descriptions using weighted fit scoring and skill-gap insights."
  },
  {
    title: "Fraud Detection",
    description: "Score suspicious job postings with ML + rule-driven risk drivers and trust-signal explanations."
  }
];

export default function HomePage() {
  return (
    <MarketingLayout>
      <section className="relative overflow-hidden">
        <div className="mx-auto w-full max-w-7xl px-4 pb-16 pt-14 md:px-8 md:pb-20 md:pt-20">
          <div className="grid gap-8 md:grid-cols-[1.2fr,0.8fr] md:items-center">
            <div className="fade-up space-y-5">
              <p className="inline-flex rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-teal-800">
                Recruitment Intelligence Platform
              </p>
              <h1 className="font-display text-4xl font-extrabold leading-tight text-ink md:text-6xl">
                Turn Hiring Data Into Confident Decisions.
              </h1>
              <p className="max-w-xl text-base text-slate-600 md:text-lg">
                A modern web platform to parse resumes, generate tailored resumes, score candidate-job fit, and detect risky job posts.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link
                  to="/app/resume-ai"
                  className="rounded-xl bg-orange-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-orange-700"
                >
                  Start With Resume AI
                </Link>
                <Link
                  to="/features"
                  className="rounded-xl border border-website-edge bg-white px-5 py-3 text-sm font-bold text-slate-700 transition hover:bg-teal-50"
                >
                  Explore Features
                </Link>
              </div>
            </div>

            <div className="fade-up rounded-3xl border border-website-edge bg-white p-5 shadow-lift-lg">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Live Capability Snapshot</p>
              <div className="mt-4 grid gap-3">
                <div className="rounded-xl border border-website-edge bg-gradient-to-r from-teal-100 to-teal-50 p-3">
                  <p className="text-xs text-slate-600">Resume Intelligence Score</p>
                  <p className="font-display text-2xl font-bold text-teal-900">0-100</p>
                </div>
                <div className="rounded-xl border border-website-edge bg-gradient-to-r from-orange-100 to-orange-50 p-3">
                  <p className="text-xs text-slate-600">Candidate-Role Match Fit</p>
                  <p className="font-display text-2xl font-bold text-orange-900">Weighted + Explainable</p>
                </div>
                <div className="rounded-xl border border-website-edge bg-gradient-to-r from-slate-100 to-white p-3">
                  <p className="text-xs text-slate-600">Job Scam Probability</p>
                  <p className="font-display text-2xl font-bold text-slate-900">ML Risk Screening</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-7xl px-4 pb-14 md:px-8 md:pb-16">
        <div className="grid gap-4 md:grid-cols-4">
          {featureCards.map((item) => (
            <article key={item.title} className="fade-up rounded-2xl border border-website-edge bg-white p-4 shadow-soft">
              <p className="font-display text-lg font-bold text-ink">{item.title}</p>
              <p className="mt-2 text-sm text-slate-600">{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto w-full max-w-7xl px-4 pb-20 md:px-8">
        <div className="rounded-3xl border border-website-edge bg-slate-950 p-6 text-slate-100 md:p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal-200">Workflow</p>
          <h2 className="mt-2 font-display text-2xl font-bold md:text-3xl">One Flow From Resume Intake To Hiring Confidence</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-orange-200">Step 1</p>
              <p className="mt-1 font-display text-lg font-bold">Collect Candidate Data</p>
              <p className="mt-1 text-sm text-slate-300">Upload resume or create one in Resume AI with structured role-ready sections.</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-orange-200">Step 2</p>
              <p className="mt-1 font-display text-lg font-bold">Target The Right Role</p>
              <p className="mt-1 text-sm text-slate-300">Analyze job descriptions and surface fit score, required overlap, and missing capabilities.</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-orange-200">Step 3</p>
              <p className="mt-1 font-display text-lg font-bold">Reduce Hiring Risk</p>
              <p className="mt-1 text-sm text-slate-300">Run fake-job detection and keep your pipeline safer for candidates and recruiters.</p>
            </div>
          </div>
          <div className="mt-6">
            <Link
              to="/app/resume-scanner"
              className="inline-flex rounded-xl bg-teal-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-teal-700"
            >
              Enter App Workspace
            </Link>
          </div>
        </div>
      </section>
    </MarketingLayout>
  );
}
