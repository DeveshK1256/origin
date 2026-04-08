export default function ErrorAlert({ message }) {
  if (!message) return null;

  return (
    <div className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
      {message}
    </div>
  );
}
