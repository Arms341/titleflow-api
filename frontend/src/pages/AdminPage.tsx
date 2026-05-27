// AdminPage.tsx v1.1.0
// Admin dashboard — stats overview, agent management, fee settings.
// v1.1.0: Added Fee Settings tab with editable fees, endorsement toggles, seller line item toggles.
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useState } from 'react';
import { Users, FileText, ShoppingBag, TrendingUp, CheckCircle, XCircle, RefreshCw, Settings, Save, DollarSign } from 'lucide-react';

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
  const [tab, setTab] = useState<'overview' | 'agents' | 'settings'>('overview');
  const { data: stats, isLoading: statsLoading } = useQuery({ queryKey: ['admin-stats'], queryFn: () => api.get('/admin/stats').then(r => r.data) });
  const { data: agents, isLoading: agentsLoading } = useQuery({ queryKey: ['admin-agents'], queryFn: () => api.get('/auth/agents').then(r => r.data) });
  const { data: topAgents } = useQuery({ queryKey: ['admin-top-agents'], queryFn: () => api.get('/admin/top-agents').then(r => r.data) });
  const approveMutation = useMutation({ mutationFn: (id: number) => api.put(`/auth/agents/${id}/approve`), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-agents'] }); queryClient.invalidateQueries({ queryKey: ['admin-stats'] }); } });
  const deactivateMutation = useMutation({ mutationFn: (id: number) => api.put(`/auth/agents/${id}/deactivate`), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-agents'] }); queryClient.invalidateQueries({ queryKey: ['admin-stats'] }); } });
  const agentList = Array.isArray(agents) ? agents : [];
  const topList = Array.isArray(topAgents) ? topAgents : [];
  if (statsLoading) return <div className="p-6 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto" /></div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Admin Dashboard</h1>
      <p className="text-gray-500 mb-6">Agent management, analytics, and fee configuration</p>
      <div className="flex gap-1 mb-6 border-b">
        <button onClick={() => setTab('overview')} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'overview' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Overview</button>
        <button onClick={() => setTab('agents')} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'agents' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
          Agents {stats?.agents?.pending_approval > 0 && <span className="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">{stats.agents.pending_approval}</span>}
        </button>
        <button onClick={() => setTab('settings')} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'settings' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
          <Settings size={14} className="inline mr-1 mb-0.5" />Fee Settings
        </button>
      </div>

      {tab === 'overview' && stats && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard icon={Users} label="Active Agents" value={stats.agents.active} sub={`${stats.agents.pending_approval} pending approval`} color="bg-blue-500" />
            <StatCard icon={FileText} label="Sheets This Month" value={stats.sheets.this_month} sub={`${stats.sheets.total} total`} color="bg-emerald-500" />
            <StatCard icon={ShoppingBag} label="Orders This Month" value={stats.orders.this_month} sub={`${stats.orders.pending} pending`} color="bg-amber-500" />
            <StatCard icon={TrendingUp} label="Conversion Rate" value={`${stats.conversion_rate}%`} sub="Sheets to orders" color="bg-purple-500" />
          </div>
          {topList.length > 0 && (
            <div className="bg-white rounded-lg shadow border overflow-hidden">
              <div className="px-4 py-3 border-b bg-gray-50"><h2 className="font-semibold text-gray-700">Top Agents by Volume</h2></div>
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Brokerage</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sheets</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Orders</th></tr></thead>
                <tbody className="divide-y divide-gray-200">
                  {topList.map((a: any) => (<tr key={a.id} className="hover:bg-gray-50"><td className="px-4 py-3 text-sm"><span className="font-medium text-gray-900">{a.full_name || a.email}</span></td><td className="px-4 py-3 text-sm text-gray-600">{a.brokerage_name || '-'}</td><td className="px-4 py-3 text-sm font-semibold">{a.sheet_count}</td><td className="px-4 py-3 text-sm font-semibold">{a.order_count}</td></tr>))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === 'agents' && (
        <div className="bg-white rounded-lg shadow border overflow-hidden">
          {agentsLoading ? (<div className="p-6 text-center"><RefreshCw size={20} className="animate-spin mx-auto text-gray-400" /></div>
          ) : agentList.length === 0 ? (<div className="p-12 text-center text-gray-500">No agents registered yet</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50"><tr><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Brokerage</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">License</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th><th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th></tr></thead>
              <tbody className="divide-y divide-gray-200">
                {agentList.map((a: any) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{a.full_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{a.email}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{a.brokerage_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{a.license_number || '-'}</td>
                    <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-medium ${a.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-yellow-100 text-yellow-800'}`}>{a.is_active ? 'Active' : 'Pending'}</span></td>
                    <td className="px-4 py-3 text-sm text-gray-500">{a.created_at ? new Date(a.created_at).toLocaleDateString() : '-'}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {!a.is_active && (<button onClick={() => approveMutation.mutate(a.id)} className="flex items-center gap-1 px-2 py-1 text-xs bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200"><CheckCircle size={12} /> Approve</button>)}
                        {a.is_active && a.role !== 'admin' && (<button onClick={() => { if (confirm(`Deactivate ${a.email}?`)) deactivateMutation.mutate(a.id); }} className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"><XCircle size={12} /> Deactivate</button>)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'settings' && <FeeSettingsPanel />}
    </div>
  );
}

function FeeInput({ label, value, onChange, prefix }: { label: string; value: number; onChange: (v: number) => void; prefix?: string }) {
  const p = prefix || '\u0024';
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="relative">
        {p && <span className="absolute left-3 top-2 text-gray-400 text-sm">{p}</span>}
        <input type="number" step="0.01" value={value} onChange={e => onChange(parseFloat(e.target.value) || 0)}
          className={`w-full ${p ? 'pl-7' : 'pl-3'} pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500`} />
      </div>
    </div>
  );
}

function FeeSettingsPanel() {
  const queryClient = useQueryClient();
  const { data: fees, isLoading } = useQuery({ queryKey: ['admin-fee-settings'], queryFn: () => api.get('/admin/fee-settings').then(r => r.data) });
  const [form, setForm] = useState<any>(null);
  const [saved, setSaved] = useState(false);
  if (fees && !form) setForm({ ...fees });
  const saveMutation = useMutation({
    mutationFn: (data: any) => api.put('/admin/fee-settings', data).then(r => r.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-fee-settings'] }); setSaved(true); setTimeout(() => setSaved(false), 3000); },
  });
  if (isLoading || !form) return <div className="p-6 text-center"><RefreshCw size={20} className="animate-spin mx-auto text-gray-400" /></div>;
  const u = (key: string, val: any) => { setForm((p: any) => ({ ...p, [key]: val })); setSaved(false); };
  const uEnd = (key: string, field: string, val: any) => { setForm((p: any) => ({ ...p, endorsements: { ...p.endorsements, [key]: { ...p.endorsements[key], [field]: val } } })); setSaved(false); };
  const uToggle = (key: string, val: boolean) => { setForm((p: any) => ({ ...p, seller_toggles: { ...p.seller_toggles, [key]: val } })); setSaved(false); };
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow border p-6">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2"><DollarSign size={18} />Closing Fees</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <FeeInput label="Closing Fee (per side)" value={form.closing_fee_per_side} onChange={v => u('closing_fee_per_side', v)} />
          <FeeInput label="Recording Fee" value={form.recording_fee} onChange={v => u('recording_fee', v)} />
          <FeeInput label="Deed Prep Fee" value={form.deed_prep_fee} onChange={v => u('deed_prep_fee', v)} />
          <FeeInput label="Release Prep Fee" value={form.release_prep_fee} onChange={v => u('release_prep_fee', v)} />
          <FeeInput label="Tax Certificate Fee" value={form.tax_cert_fee} onChange={v => u('tax_cert_fee', v)} />
          <FeeInput label="E-Recording (Seller)" value={form.e_recording_fee_seller} onChange={v => u('e_recording_fee_seller', v)} />
          <FeeInput label="E-Recording (Buyer)" value={form.e_recording_fee_buyer} onChange={v => u('e_recording_fee_buyer', v)} />
          <FeeInput label="TX Policy Guaranty Fee" value={form.guaranty_fee} onChange={v => u('guaranty_fee', v)} />
          <FeeInput label="Survey Fee" value={form.survey_fee} onChange={v => u('survey_fee', v)} />
          <FeeInput label="Default Home Warranty" value={form.default_home_warranty} onChange={v => u('default_home_warranty', v)} />
        </div>
      </div>
      <div className="bg-white rounded-lg shadow border p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Buyer / Lender Fees</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <FeeInput label="Appraisal Fee" value={form.appraisal_fee} onChange={v => u('appraisal_fee', v)} />
          <FeeInput label="Credit Report Fee" value={form.credit_report_fee} onChange={v => u('credit_report_fee', v)} />
          <FeeInput label="Flood Cert Fee" value={form.flood_cert_fee} onChange={v => u('flood_cert_fee', v)} />
          <FeeInput label="Origination Rate" value={form.origination_rate_pct} onChange={v => u('origination_rate_pct', v)} prefix="%" />
          <FeeInput label="Default Per Diem Rate" value={form.default_per_diem_rate_pct} onChange={v => u('default_per_diem_rate_pct', v)} prefix="%" />
        </div>
      </div>
      <div className="bg-white rounded-lg shadow border p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Title Endorsements (Buyer Side)</h3>
        <div className="space-y-3">
          {Object.entries(form.endorsements || {}).map(([key, end]: [string, any]) => (
            <div key={key} className="flex items-center gap-4 py-2 border-b border-gray-100 last:border-0">
              <label className="flex items-center gap-2 min-w-[200px]"><input type="checkbox" checked={end.enabled} onChange={e => uEnd(key, 'enabled', e.target.checked)} /><span className="text-sm font-medium">{end.label}</span></label>
              <div className="relative w-32"><span className="absolute left-3 top-1.5 text-gray-400 text-sm">{'\u0024'}</span><input type="number" step="0.01" value={end.amount} onChange={e => uEnd(key, 'amount', parseFloat(e.target.value) || 0)} className="w-full pl-7 pr-3 py-1.5 border border-gray-300 rounded text-sm" /></div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-lg shadow border p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Seller Net Sheet Line Items</h3>
        <p className="text-sm text-gray-500 mb-3">Toggle which fees appear on the seller net sheet</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {Object.entries(form.seller_toggles || {}).map(([key, enabled]: [string, any]) => (
            <label key={key} className="flex items-center gap-2 text-sm py-1"><input type="checkbox" checked={enabled} onChange={e => uToggle(key, e.target.checked)} />{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</label>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button onClick={() => saveMutation.mutate(form)} disabled={saveMutation.isPending}
          className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm disabled:opacity-50">
          <Save size={16} />{saveMutation.isPending ? 'Saving...' : 'Save Fee Settings'}
        </button>
        {saved && <span className="text-emerald-600 text-sm font-medium flex items-center gap-1"><CheckCircle size={16} /> Settings saved!</span>}
        {saveMutation.isError && <span className="text-red-600 text-sm">Save failed</span>}
      </div>
    </div>
  );
}
