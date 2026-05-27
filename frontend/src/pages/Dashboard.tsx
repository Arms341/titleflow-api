import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: string; color: string }) {
  return (
    <div className={`${color} rounded-lg p-5 border`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{label}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  );
}

function formatCurrency(val: number | string | undefined | null): string {
  if (val === undefined || val === null) return '$0.00';
  const n = typeof val === 'string' ? parseFloat(val) : val;
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<string>('checking...');

  useEffect(() => {
    api.get('/health').then(() => setHealth('healthy')).catch(() => setHealth('offline'));
  }, []);

  const { data: sheets } = useQuery({
    queryKey: ['saved-sheets'],
    queryFn: () => api.get('/saved_sheets/').then(r => r.data),
  });

  const { data: orders } = useQuery({
    queryKey: ['orders'],
    queryFn: () => api.get('/orders/').then(r => r.data),
  });

  const { data: company } = useQuery({
    queryKey: ['company'],
    queryFn: () => api.get('/company/').then(r => r.data),
  });

  const sheetList = Array.isArray(sheets) ? sheets : sheets?.items ?? [];
  const orderList = Array.isArray(orders) ? orders : orders?.items ?? [];
  const activeOrders = orderList.filter((o: any) => !['closed', 'cancelled'].includes(o.status));
  const companyName = company?.company_name || 'Title Company';

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Welcome to {companyName}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${health === 'healthy' ? 'bg-green-500' : health === 'offline' ? 'bg-red-500' : 'bg-yellow-500'}`} />
          <span className="text-xs text-gray-500">{health === 'healthy' ? 'Online' : health}</span>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard label="Sheets Generated" value={sheetList.length} icon="📄" color="bg-blue-50 border-blue-200" />
        <StatCard label="Orders Submitted" value={orderList.length} icon="📋" color="bg-emerald-50 border-emerald-200" />
        <StatCard label="Active Orders" value={activeOrders.length} icon="⚡" color="bg-amber-50 border-amber-200" />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <button onClick={() => navigate('/calculators', { state: { openCalc: 'seller-net-sheet' } })}
          className="flex items-center gap-4 p-6 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-md">
          <span className="text-4xl">🏠</span>
          <div className="text-left">
            <p className="text-lg font-semibold">New Seller Net Sheet</p>
            <p className="text-indigo-200 text-sm">Calculate seller net proceeds</p>
          </div>
        </button>
        <button onClick={() => navigate('/calculators', { state: { openCalc: 'buyer-estimate' } })}
          className="flex items-center gap-4 p-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-md">
          <span className="text-4xl">🔑</span>
          <div className="text-left">
            <p className="text-lg font-semibold">New Buyer Estimate</p>
            <p className="text-blue-200 text-sm">Estimate buyer closing costs</p>
          </div>
        </button>
      </div>

      {/* Recent Sheets */}
      <div className="bg-white rounded-lg shadow border">
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Recent Sheets</h2>
          {sheetList.length > 0 && (
            <button onClick={() => navigate('/saved-sheets')} className="text-sm text-indigo-600 hover:text-indigo-800">
              View All →
            </button>
          )}
        </div>
        {sheetList.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-4xl mb-3">📝</p>
            <p className="text-gray-500 mb-1">No sheets generated yet</p>
            <p className="text-gray-400 text-sm">Create your first net sheet or buyer estimate from the Calculators page</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Property</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sheetList.slice(0, 10).map((sheet: any) => (
                  <tr key={sheet.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate('/saved-sheets', { state: { viewSheet: sheet } })}>
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">{sheet.property_address || 'No address'}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        sheet.sheet_type === 'seller' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'
                      }`}>{sheet.sheet_type || 'Sheet'}</span>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {formatCurrency(sheet.net_proceeds || sheet.cash_to_close || sheet.total_closing_costs)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {sheet.created_at ? new Date(sheet.created_at).toLocaleDateString() : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
