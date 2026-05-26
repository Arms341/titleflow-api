import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useState } from 'react';

const fmt = (v: any) => { if (v == null) return '-'; const n = typeof v === 'string' ? parseFloat(v) : v; if (isNaN(n)) return '-'; return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n); };

function SheetDetail({ sheet, onBack }: { sheet: any; onBack: () => void }) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const out = sheet.output_data || {};
  const inp = sheet.input_data || {};

  const handleShare = async () => {
    try {
      const res = await api.post(`/saved_sheets/${sheet.id}/share`);
      const url = res.data.share_url || `${window.location.origin}/shared/${res.data.share_token}`;
      setShareUrl(url);
      navigator.clipboard.writeText(url).catch(() => {});
    } catch (e: any) { alert('Share failed: ' + (e.response?.data?.detail || e.message)); }
  };

  const handlePdf = async () => {
    setDownloading(true);
    try {
      const res = await api.get(`/saved_sheets_export/${sheet.id}/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a'); a.href = url; a.download = `sheet_${sheet.id}.pdf`; a.click();
      window.URL.revokeObjectURL(url);
    } catch (e: any) { alert('PDF failed: ' + (e.response?.data?.detail || e.message)); }
    setDownloading(false);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button onClick={onBack} className="text-sm text-indigo-600 hover:text-indigo-800 mb-4">← Back to My Sheets</button>

      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${sheet.sheet_type === 'seller' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}`}>
              {sheet.sheet_type === 'seller' ? 'Seller Net Sheet' : 'Buyer Estimate'}
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">{sheet.property_address || 'No address'}</h2>
            <p className="text-gray-500 text-sm">{sheet.client_name || 'No client name'} • {sheet.created_at ? new Date(sheet.created_at).toLocaleDateString() : ''}</p>
          </div>
          <div className="text-right">
            {out.net_proceeds != null && (
              <div><p className="text-xs text-gray-500 uppercase">Net Proceeds</p><p className="text-2xl font-bold text-emerald-600">{fmt(out.net_proceeds)}</p></div>
            )}
            {out.cash_to_close != null && (
              <div><p className="text-xs text-gray-500 uppercase">Cash to Close</p><p className="text-2xl font-bold text-blue-600">{fmt(out.cash_to_close)}</p></div>
            )}
          </div>
        </div>

        {/* Line items */}
        {out.line_items?.length > 0 && (
          <div className="mb-6">
            <h3 className="font-semibold text-gray-700 text-sm uppercase mb-2">Breakdown</h3>
            <div className="bg-gray-50 rounded-lg border p-4 space-y-1">
              {out.line_items.map((item: any, i: number) => (
                <div key={i} className="flex justify-between text-sm py-1 border-b border-gray-200 last:border-0">
                  <span className="text-gray-700">{item.label}</span>
                  <span className="font-medium">{fmt(item.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="bg-gray-50 rounded-lg border p-4 space-y-2 mb-6">
          <h3 className="font-semibold text-gray-700 text-sm uppercase mb-2">Summary</h3>
          {out.sale_price != null && <div className="flex justify-between text-sm"><span>Sale Price</span><span className="font-semibold">{fmt(out.sale_price)}</span></div>}
          {out.purchase_price != null && <div className="flex justify-between text-sm"><span>Purchase Price</span><span className="font-semibold">{fmt(out.purchase_price)}</span></div>}
          {out.total_closing_costs != null && <div className="flex justify-between text-sm"><span>Total Closing Costs</span><span className="font-semibold text-red-600">-{fmt(out.total_closing_costs)}</span></div>}
          {out.loan_payoff != null && <div className="flex justify-between text-sm"><span>Loan Payoff</span><span className="font-semibold text-red-600">-{fmt(out.loan_payoff)}</span></div>}
          {out.net_proceeds != null && <div className="flex justify-between text-lg font-bold pt-2 border-t"><span>Net Proceeds</span><span className="text-emerald-600">{fmt(out.net_proceeds)}</span></div>}
          {out.cash_to_close != null && <div className="flex justify-between text-lg font-bold pt-2 border-t"><span>Cash to Close</span><span className="text-blue-600">{fmt(out.cash_to_close)}</span></div>}
        </div>

        {/* Input summary */}
        {Object.keys(inp).length > 0 && (
          <details className="mb-6">
            <summary className="cursor-pointer text-sm font-semibold text-gray-500 hover:text-gray-700">View Input Parameters</summary>
            <div className="mt-2 bg-gray-50 rounded-lg border p-4 grid grid-cols-2 gap-2 text-sm">
              {Object.entries(inp).filter(([k]) => !['save'].includes(k)).map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-gray-200 py-1">
                  <span className="text-gray-600">{k.replace(/_/g, ' ')}</span>
                  <span className="font-medium text-gray-900">{typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)}</span>
                </div>
              ))}
            </div>
          </details>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <button onClick={handleShare} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm">🔗 Share with Client</button>
          <button onClick={handlePdf} disabled={downloading} className="flex items-center gap-2 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium text-sm">
            {downloading ? 'Generating...' : '📄 Download PDF'}
          </button>
          <button onClick={() => { const mailto = `mailto:?subject=Net Sheet - ${sheet.property_address || 'Property'}&body=View your net sheet here: ${shareUrl || 'Please generate a share link first'}`; window.open(mailto); }}
            className="flex items-center gap-2 px-4 py-2.5 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium text-sm">✉️ Email to Client</button>
        </div>

        {shareUrl && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 font-medium">Share link copied to clipboard!</p>
            <a href={shareUrl} target="_blank" rel="noreferrer" className="text-xs text-blue-600 underline break-all">{shareUrl}</a>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SavedSheetPage() {
  const queryClient = useQueryClient();
  const [viewing, setViewing] = useState<any>(null);

  const { data: sheets, isLoading } = useQuery({
    queryKey: ['saved-sheets'],
    queryFn: () => api.get('/saved_sheets/').then(r => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/saved_sheets/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['saved-sheets'] }),
  });

  const list = Array.isArray(sheets) ? sheets : sheets?.items ?? [];

  if (viewing) return <SheetDetail sheet={viewing} onBack={() => setViewing(null)} />;
  if (isLoading) return <div className="p-6 text-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto" /></div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">My Sheets</h1>
      <p className="text-gray-500 mb-6">{list.length} saved sheet{list.length !== 1 ? 's' : ''}</p>

      {list.length === 0 ? (
        <div className="text-center p-12 bg-gray-50 rounded-lg border">
          <p className="text-4xl mb-3">📝</p>
          <p className="text-gray-500">No saved sheets yet</p>
          <p className="text-gray-400 text-sm mt-1">Calculate a net sheet or buyer estimate, then click Save</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Property</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {list.map((s: any) => {
                const amount = s.output_data?.net_proceeds || s.output_data?.cash_to_close || s.output_data?.total_closing_costs;
                return (
                  <tr key={s.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setViewing(s)}>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${s.sheet_type === 'seller' ? 'bg-emerald-100 text-emerald-800' : s.sheet_type === 'buyer' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
                        {s.sheet_type || 'Sheet'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-medium">{s.property_address || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{s.client_name || '-'}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-gray-900">{fmt(amount)}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{s.created_at ? new Date(s.created_at).toLocaleDateString() : '-'}</td>
                    <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                      <div className="flex gap-1">
                        <button onClick={() => setViewing(s)} className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200" title="View">👁️</button>
                        <button onClick={() => { if (confirm('Delete this sheet?')) deleteMutation.mutate(s.id); }} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200" title="Delete">🗑️</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
