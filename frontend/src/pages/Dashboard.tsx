// Universal Dashboard v1.0.0
// Locked UNIVERSAL template — generic dashboard for any gig type.
// Gig-specific dashboards override this via gig_type in template.json.
import { useEffect, useState } from 'react';
import api from '@/lib/api';

export default function Dashboard() {
  const [health, setHealth] = useState<string>('checking...');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.get('/health');
        setHealth(res.data?.status === 'healthy' ? 'healthy' : 'degraded');
      } catch {
        setHealth('offline');
      } finally {
        setLoading(false);
      }
    };
    checkHealth();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${
            health === 'healthy' ? 'bg-green-500' :
            health === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-sm font-medium text-gray-600">
            API Status: {health}
          </span>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Welcome</h2>
        <p className="text-gray-600">
          Your application is running. Use the navigation to explore features.
        </p>
      </div>
    </div>
  );
}
