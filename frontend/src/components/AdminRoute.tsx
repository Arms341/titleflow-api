// JARVIS App — Admin-only Route Guard
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';

interface Props { children: React.ReactNode }

export default function AdminRoute({ children }: Props) {
  const { isAuthenticated, isLoading, isAdmin } = useAuth();

  if (isLoading) return <LoadingSpinner fullPage />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/dashboard" replace />;

  return <>{children}</>;
}
