// AdminPage.tsx v1.0.0
// Admin dashboard — stats overview, agent list with approve/deactivate, top agents.
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useState } from 'react';
import { Users, FileText, ShoppingBag, TrendingUp, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

function StatCard({ icon: Icon, label, value, sub, color }: { icon: any; label: string; value: number | string; sub?: string; color: string }) {
  return (
    <div className="bg-white rounded-lg shadow border p-5">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${color}`}><Icon size={20} className="text-white" /></div>
        <span className="text-sm font-medium text-gray-500">{label}</span>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'overview' | 'agents'>('overview');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => api.get('/admin/stats').then(r => r.data),
  });

  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['admin-agents'],
    queryFn: () => api.get('/auth/agents').then(r => r.data),
  });

  const { data: topAgents } = useQuery({
    queryKey: ['admin-top-agents'],
    queryFn: () => api.get('/admin/top-agents').then(r => r.data),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => api.put(`/auth/agents/${id}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => api.put(`/auth/agents/${id}/deactivate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
    },
  });

  const agentList = Array.isArray(agents) ? agents : [];
  const topList = Array.isArray(topAgents) ? topAgents : [];

  if (statsLoading) return <div className="p-6 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto" /></div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Admin Dashboard</h1>
      <p className="text-gray-500 mb-6">Agent management and analytics</p>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b">
        <button onClick={() => setTab('overview')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'overview' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
          Overview
        </button>
        <button onClick={() => setTab('agents')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'agents' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
          Agents {stats?.agents?.pending_approval > 0 && <span className="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">{stats.agents.pending_approval}</span>}
        </button>
      </div>

      {tab === 'overview' && stats && (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard icon={Users} label="Active Agents" value={stats.agents.active} sub={`${stats.agents.pending_approval} pending approval`} color="bg-blue-500" />
            <StatCard icon={FileText} label="Sheets This Month" value={stats.sheets.this_month} sub={`${stats.sheets.total} total`} color="bg-emerald-500" />
            <StatCard icon={ShoppingBag} label="Orders This Month" value={stats.orders.this_month} sub={`${stats.orders.pending} pending`} color="bg-amber-500" />
            <StatCard icon={TrendingUp} label="Conversion Rate" value={`${stats.conversion_rate}%`} sub="Sheets to orders" color="bg-purple-500" />
          </div>

          {/* Top Agents */}
          {topList.length > 0 && (
            <div className="bg-white rounded-lg shadow border overflow-hidden">
              <div className="px-4 py-3 border-b bg-gray-50">
                <h2 className="font-semibold text-gray-700">Top Agents by Volume</h2>
              </div>
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Brokerage</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sheets</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Orders</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {topList.map((a: any) => (
                    <tr key={a.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm"><span className="font-medium text-gray-900">{a.full_name || a.email}</span></td>
                      <td className="px-4 py-3 text-sm text-gray-600">{a.brokerage_name || '-'}</td>
                      <td className="px-4 py-3 text-sm font-semibold">{a.sheet_count}</td>
                      <td className="px-4 py-3 text-sm font-semibold">{a.order_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === 'agents' && (
        <div className="bg-white rounded-lg shadow border overflow-hidden">
          {agentsLoading ? (
            <div className="p-6 text-center"><RefreshCw size={20} className="animate-spin mx-auto text-gray-400" /></div>
          ) : agentList.length === 0 ? (
            <div className="p-12 text-center text-gray-500">No agents registered yet</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Brokerage</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">License</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {agentList.map((a: any) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{a.full_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{a.email}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{a.brokerage_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{a.license_number || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${a.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-yellow-100 text-yellow-800'}`}>
                        {a.is_active ? 'Active' : 'Pending'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{a.created_at ? new Date(a.created_at).toLocaleDateString() : '-'}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {!a.is_active && (
                          <button onClick={() => approveMutation.mutate(a.id)}
                            className="flex items-center gap-1 px-2 py-1 text-xs bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200"
                            title="Approve">
                            <CheckCircle size={12} /> Approve
                          </button>
                        )}
                        {a.is_active && a.role !== 'admin' && (
                          <button onClick={() => { if (confirm(`Deactivate ${a.email}?`)) deactivateMutation.mutate(a.id); }}
                            className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                            title="Deactivate">
                            <XCircle size={12} /> Deactivate
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
