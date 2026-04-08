export default function LoadingSpinner({ label = "Loading..." }) {
  return (
    <div className="inline-flex items-center gap-3 rounded-xl border border-edge bg-white px-4 py-2 text-sm text-slate-700">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-teal-600 border-r-transparent" />
      {label}
    </div>
  );
}
