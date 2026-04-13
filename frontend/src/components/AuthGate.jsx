import { useState } from "react";

export default function AuthGate({ onSignIn, onSignUp, loading, authError }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("signin");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!email.trim() || !password.trim()) {
      return;
    }

    if (mode === "signup") {
      await onSignUp?.(email.trim(), password);
      return;
    }
    await onSignIn?.(email.trim(), password);
  };

  return (
    <div className="min-h-screen bg-mist px-4 py-12 text-ink">
      <div className="mx-auto w-full max-w-md rounded-3xl border border-edge bg-white p-6 shadow-lift">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">Supabase Auth</p>
        <h1 className="mt-2 font-display text-3xl font-bold">Welcome Back</h1>
        <p className="mt-1 text-sm text-slate-600">
          Sign in to use Resume Scanner, Job Analyzer, Fake Job Detection, and Resume AI.
        </p>

        <div className="mt-4 flex gap-2 rounded-xl bg-panel p-1">
          <button
            type="button"
            onClick={() => setMode("signin")}
            className={`w-full rounded-lg px-3 py-2 text-sm font-semibold transition ${
              mode === "signin" ? "bg-teal-700 text-white" : "text-slate-700 hover:bg-white"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={`w-full rounded-lg px-3 py-2 text-sm font-semibold transition ${
              mode === "signup" ? "bg-teal-700 text-white" : "text-slate-700 hover:bg-white"
            }`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <label className="block text-sm font-semibold text-slate-700">
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
              placeholder="you@example.com"
            />
          </label>

          <label className="block text-sm font-semibold text-slate-700">
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 block w-full rounded-xl border border-edge bg-panel px-3 py-2 text-sm"
              placeholder="********"
            />
          </label>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Please wait..." : mode === "signup" ? "Create Account" : "Sign In"}
          </button>

          {authError ? (
            <p className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{authError}</p>
          ) : null}

          <p className="text-xs text-slate-500">
            In signup mode, Supabase may send a confirmation email depending on your project settings.
          </p>
        </form>
      </div>
    </div>
  );
}
