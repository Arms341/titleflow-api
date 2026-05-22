// JARVIS App — Home / Dashboard placeholder
// AI replaces this with domain-specific dashboard content.
import { useAuth } from '@/contexts/AuthContext';
import { useBrand } from '@/contexts/BrandContext';

export default function Home() {
  const { user } = useAuth();
  const { company } = useBrand();

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">
        Welcome, {user?.full_name}
      </h1>
      <p className="text-gray-500 mb-8">
        {company?.company_name || 'JARVIS App'} — Dashboard
      </p>
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
        Dashboard content goes here.
      </div>
    </div>
  );
}
