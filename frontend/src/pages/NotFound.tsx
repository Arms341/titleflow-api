// JARVIS App — 404 Not Found
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <p className="text-6xl font-bold text-[var(--color-brand)] mb-4">404</p>
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Page not found</h1>
        <p className="text-gray-500 mb-6">The page you're looking for doesn't exist.</p>
        <Link
          to="/dashboard"
          className="inline-block px-6 py-2.5 bg-[var(--color-brand)] text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
