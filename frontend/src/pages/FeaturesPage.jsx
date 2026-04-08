import { Link } from "react-router-dom";
import MarketingLayout from "../components/MarketingLayout";

const features = [
  {
    title: "Resume Scanner",
    subtitle: "Extract signal from unstructured resumes",
    points: [
      "Skill, education, project, and experience extraction",
      "Domain employability probability and strengths",
      "Recommended roles with actionable skill gaps"
    ]
  },
  {
    title: "Resume AI",
    subtitle: "Generate targeted resumes with output control",
    points: [
      "Start from scratch or parse an existing resume",
      "Target a job description for role-focused tailoring",
      "Download LaTeX and DOCX, then refine in Overleaf"
    ]
  },
  {
    title: "Job Analyzer",
    subtitle: "Understand role quality and candidate fit",
    points: [
      "Required/preferred skills and seniority analysis",
      "Weighted fit scoring with domain alignment",
      "Critical gaps and next-step recommendations"
    ]
  },
  {
    title: "Fake Job Detection",
    subtitle: "Flag risky postings before engagement",
    points: [
      "ML + rule hybrid scoring",
      "Red flags, trust signals, and confidence levels",
      "Driver-level explanation for auditability"
    ]
  }
];

export default function FeaturesPage() {
  return (
    <MarketingLayout>
      <section className="mx-auto w-full max-w-7xl px-4 pb-20 pt-14 md:px-8 md:pt-16">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal-700">Features</p>
          <h1 className="mt-2 font-display text-4xl font-extrabold text-ink md:text-5xl">
            A full hiring intelligence stack, not a single utility.
          </h1>
          <p className="mt-3 text-base text-slate-600">
            Each module is designed to work independently and as part of one end-to-end hiring workflow.
          </p>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {features.map((item) => (
            <article key={item.title} className="rounded-2xl border border-website-edge bg-white p-5 shadow-soft">
              <p className="font-display text-2xl font-bold text-ink">{item.title}</p>
              <p className="mt-1 text-sm font-semibold text-teal-700">{item.subtitle}</p>
              <ul className="mt-3 space-y-2 text-sm text-slate-700">
                {item.points.map((point) => (
                  <li key={point}>- {point}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>

        <div className="mt-8 rounded-2xl border border-website-edge bg-gradient-to-r from-teal-100 via-white to-orange-100 p-5">
          <p className="font-display text-xl font-bold text-ink">Ready to run the complete workflow?</p>
          <p className="mt-1 text-sm text-slate-700">Open the app workspace and start with Resume AI or Resume Scanner.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              to="/app/resume-ai"
              className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800"
            >
              Open Resume AI
            </Link>
            <Link
              to="/app/resume-scanner"
              className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-700"
            >
              Open Resume Scanner
            </Link>
          </div>
        </div>
      </section>
    </MarketingLayout>
  );
}
