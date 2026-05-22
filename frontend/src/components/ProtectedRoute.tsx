// JARVIS App — Protected Route
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';

interface Props { children: React.ReactNode }

export default function ProtectedRoute({ children }: Props) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) return <LoadingSpinner fullPage />;

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Account exists but pending approval
  if (user?.status === 'pending_approval') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md text-center p-8 bg-white rounded-2xl shadow">
          <div className="text-4xl mb-4">⏳</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Account Pending Approval</h2>
          <p className="text-gray-600">
            Your account is awaiting approval. You'll receive an email once activated.
          </p>
          <button
            onClick={() => { localStorage.clear(); window.location.href = '/login'; }}
            className="mt-6 text-sm text-gray-500 underline"
          >
            Back to login
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
