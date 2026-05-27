import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const fmt = (v: any) => { if (v == null) return '-'; const n = typeof v === 'string' ? parseFloat(v) : v; if (isNaN(n)) return '-'; return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n); };

// -- Full-screen signature pad for in-person signing --
function FullScreenSignature({ sheet, onClose, onSigned }: { sheet: any; onClose: () => void; onSigned: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [drawing, setDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);
  const [signerName, setSignerName] = useState(sheet.client_name || '');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const getPos = (e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    if ('touches' in e) return { x: e.touches[0].clientX - rect.left, y: e.touches[0].clientY - rect.top };
    return { x: (e as React.MouseEvent).clientX - rect.left, y: (e as React.MouseEvent).clientY - rect.top };
  };
  const start = (e: React.MouseEvent | React.TouchEvent) => { e.preventDefault(); const ctx = canvasRef.current?.getContext('2d'); if (!ctx) return; const p = getPos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); setDrawing(true); setHasDrawn(true); };
  const draw = (e: React.MouseEvent | React.TouchEvent) => { if (!drawing) return; e.preventDefault(); const ctx = canvasRef.current?.getContext('2d'); if (!ctx) return; const p = getPos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); };
  const stop = () => setDrawing(false);
  const clear = () => { const c = canvasRef.current; if (!c) return; c.getContext('2d')?.clearRect(0, 0, c.width, c.height); setHasDrawn(false); };

  const submit = async () => {
    if (!canvasRef.current || !hasDrawn) return;
    setSubmitting(true);
    try {
      await api.post(`/saved_sheets/${sheet.id}/sign`, { signature: canvasRef.current.toDataURL('image/png'), signer_name: signerName });
      setDone(true);
      setTimeout(() => { onSigned(); onClose(); }, 2000);
    } catch (e: any) { alert(e.response?.data?.detail || 'Signature failed'); }
    setSubmitting(false);
  };

  if (done) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex flex-col items-center justify-center">
        <div className="text-6xl mb-4">&#9989;</div>
        <h2 className="text-2xl font-bold text-emerald-800">Signed Successfully</h2>
        <p className="text-gray-500 mt-2">Thank you, {signerName || 'Client'}!</p>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      {/* Header */}
      <div className="bg-slate-800 text-white px-6 py-4 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-lg font-bold">Client Signature</h2>
          <p className="text-sm text-slate-300">{sheet.property_address || 'Net Sheet'}</p>
        </div>
        <button onClick={onClose} className="text-slate-300 hover:text-white text-2xl px-2">&times;</button>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-4 max-w-lg mx-auto w-full">
        <p className="text-gray-600 text-center mb-4">
          By signing below, I acknowledge that I have reviewed the {sheet.sheet_type === 'seller' ? 'seller net sheet' : 'buyer estimate'} and understand that figures shown are estimates.
        </p>

        {/* Name */}
        <div className="w-full mb-4">
          <label className="block text-sm text-gray-500 mb-1">Your Name</label>
          <input type="text" value={signerName} onChange={e => setSignerName(e.target.value)}
            placeholder="Full Name" className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg text-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
        </div>

        {/* Canvas */}
        <div className="w-full border-2 border-gray-300 rounded-lg bg-gray-50 relative mb-4" style={{ touchAction: 'none' }}>
          <canvas ref={canvasRef} className="w-full cursor-crosshair" style={{ height: '200px' }}
            onMouseDown={start} onMouseMove={draw} onMouseUp={stop} onMouseLeave={stop}
            onTouchStart={start} onTouchMove={draw} onTouchEnd={stop} />
          <div className="absolute bottom-3 left-4 right-4 border-b border-gray-400" />
          <span className="absolute bottom-1 left-4 text-xs text-gray-400">Sign here</span>
        </div>

        {/* Buttons */}
        <div className="w-full flex gap-3">
          <button onClick={clear} className="flex-1 py-3 text-gray-700 border-2 border-gray-300 rounded-lg text-base font-medium hover:bg-gray-50">Clear</button>
          <button onClick={submit} disabled={!hasDrawn || submitting}
            className="flex-[2] py-3 bg-emerald-600 text-white rounded-lg text-base font-bold hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed">
            {submitting ? 'Saving...' : 'Confirm Signature'}
          </button>
        </div>
      </div>
    </div>
  );
}

// -- Order Submission Form Modal --
function OrderFormModal({ sheet, onClose, onSuccess }: { sheet: any; onClose: () => void; onSuccess: (order: any) => void }) {
  const inp = sheet.input_data || {};
  const out = sheet.output_data || {};
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    buyer_name: sheet.sheet_type === 'buyer' ? (sheet.client_name || inp.client_name || '') : '',
    buyer_email: '',
    buyer_phone: '',
    seller_name: sheet.sheet_type === 'seller' ? (sheet.client_name || inp.client_name || '') : '',
    seller_email: '',
    seller_phone: '',
    lender_name: '',
    loan_officer_name: '',
    escrow_officer_preference: '',
    property_address: sheet.property_address || inp.property_address || '',
    contract_date: '',
    estimated_closing_date: inp.closing_date || '',
    notes: '',
  });

  const update = (field: string, value: string) => setForm(prev => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.post('/orders/', {
        ...form,
        saved_sheet_id: sheet.id,
        order_type: 'purchase',
        status: 'submitted',
        contract_date: form.contract_date || null,
        estimated_closing_date: form.estimated_closing_date || null,
      });
      onSuccess(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Submission failed');
    }
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-xl">
          <h2 className="text-lg font-bold text-gray-900">Submit Title Order</h2>
          <p className="text-sm text-gray-500">Complete the details below to submit to HUB City Title</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Property */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase mb-3">Property</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="md:col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Property Address</label>
                <input type="text" value={form.property_address} onChange={e => update('property_address', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Contract Date</label>
                <input type="date" value={form.contract_date} onChange={e => update('contract_date', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Estimated Closing Date</label>
                <input type="date" value={form.estimated_closing_date} onChange={e => update('estimated_closing_date', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </div>
          </div>

          {/* Seller */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase mb-3">Seller</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Name</label>
                <input type="text" value={form.seller_name} onChange={e => update('seller_name', e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Email</label>
                <input type="email" value={form.seller_email} onChange={e => update('seller_email', e.target.value)}
                  placeholder="jane@email.com"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Phone</label>
                <input type="tel" value={form.seller_phone} onChange={e => update('seller_phone', e.target.value)}
                  placeholder="(806) 555-1234"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </div>
          </div>

          {/* Buyer */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase mb-3">Buyer</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Name</label>
                <input type="text" value={form.buyer_name} onChange={e => update('buyer_name', e.target.value)}
                  placeholder="John Smith"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Email</label>
                <input type="email" value={form.buyer_email} onChange={e => update('buyer_email', e.target.value)}
                  placeholder="john@email.com"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Phone</label>
                <input type="tel" value={form.buyer_phone} onChange={e => update('buyer_phone', e.target.value)}
                  placeholder="(806) 555-5678"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </div>
          </div>

          {/* Lender */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase mb-3">Lender</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Lender Name</label>
                <input type="text" value={form.lender_name} onChange={e => update('lender_name', e.target.value)}
                  placeholder="First National Bank"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Loan Officer</label>
                <input type="text" value={form.loan_officer_name} onChange={e => update('loan_officer_name', e.target.value)}
                  placeholder="Mike Johnson"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Escrow Officer Preference</label>
                <input type="text" value={form.escrow_officer_preference} onChange={e => update('escrow_officer_preference', e.target.value)}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Notes for Title Company</label>
            <textarea value={form.notes} onChange={e => update('notes', e.target.value)}
              rows={3} placeholder="Any special instructions or notes..."
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none" />
          </div>

          {/* Sheet Reference */}
          <div className="bg-gray-50 rounded-lg border p-3">
            <p className="text-xs text-gray-500">
              Linked to {sheet.sheet_type === 'seller' ? 'Seller Net Sheet' : 'Buyer Estimate'} &mdash;
              {out.net_proceeds ? ` Net: ${fmt(out.net_proceeds)}` : out.cash_to_close ? ` Cash to Close: ${fmt(out.cash_to_close)}` : ''}
              {sheet.property_address ? ` at ${sheet.property_address}` : ''}
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="px-4 py-2.5 text-sm text-gray-700 border rounded-lg hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={submitting}
              className="px-6 py-2.5 bg-amber-600 text-white font-bold rounded-lg hover:bg-amber-700 shadow-md text-sm disabled:opacity-50">
              {submitting ? 'Submitting...' : 'Submit Title Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// -- Sheet Detail View --
function SheetDetail({ sheet, onBack }: { sheet: any; onBack: () => void }) {
  const navigate = useNavigate();
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [submitted, setSubmitted] = useState<any>(null);
  const [showSignature, setShowSignature] = useState(false);
  const [isSigned, setIsSigned] = useState(!!sheet.client_signature || !!sheet.signed_at);
  const out = sheet.output_data || {};
  const inp = sheet.input_data || {};

  const handleShare = async () => {
    try {
      const res = await api.post(`/saved_sheets/${sheet.id}/share`);
      const url = res.data.share_url || `${window.location.origin}/shared/${res.data.share_token}`;
      setShareUrl(url);
      const canShare = typeof navigator !== 'undefined' && 'share' in navigator;
      if (canShare) {
        await navigator.share({ title: `${sheet.sheet_type === 'seller' ? 'Seller Net Sheet' : 'Buyer Estimate'} - ${sheet.property_address || 'Property'}`, text: `View your ${sheet.sheet_type === 'seller' ? 'seller net sheet' : 'buyer estimate'} from HUB City Title`, url });
      } else {
        await navigator.clipboard.writeText(url);
      }
    } catch (e: any) { if (e.name !== 'AbortError') { try { if (shareUrl) await navigator.clipboard.writeText(shareUrl); } catch {} } }
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
      <button onClick={onBack} className="text-sm text-indigo-600 hover:text-indigo-800 mb-4">&larr; Back to My Sheets</button>

      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${sheet.sheet_type === 'seller' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}`}>
              {sheet.sheet_type === 'seller' ? 'Seller Net Sheet' : 'Buyer Estimate'}
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">{sheet.property_address || 'No address'}</h2>
            <p className="text-gray-500 text-sm">{sheet.client_name || 'No client name'} &bull; {sheet.created_at ? new Date(sheet.created_at).toLocaleDateString() : ''}</p>
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

        <div className="bg-gray-50 rounded-lg border p-4 space-y-2 mb-6">
          <h3 className="font-semibold text-gray-700 text-sm uppercase mb-2">Summary</h3>
          {out.sale_price != null && <div className="flex justify-between text-sm"><span>Sale Price</span><span className="font-semibold">{fmt(out.sale_price)}</span></div>}
          {out.purchase_price != null && <div className="flex justify-between text-sm"><span>Purchase Price</span><span className="font-semibold">{fmt(out.purchase_price)}</span></div>}
          {out.total_closing_costs != null && <div className="flex justify-between text-sm"><span>Total Closing Costs</span><span className="font-semibold text-red-600">-{fmt(out.total_closing_costs)}</span></div>}
          {out.loan_payoff != null && <div className="flex justify-between text-sm"><span>Loan Payoff</span><span className="font-semibold text-red-600">-{fmt(out.loan_payoff)}</span></div>}
          {out.net_proceeds != null && <div className="flex justify-between text-lg font-bold pt-2 border-t"><span>Net Proceeds</span><span className="text-emerald-600">{fmt(out.net_proceeds)}</span></div>}
          {out.cash_to_close != null && <div className="flex justify-between text-lg font-bold pt-2 border-t"><span>Cash to Close</span><span className="text-blue-600">{fmt(out.cash_to_close)}</span></div>}
        </div>

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

        {/* Submit to Title Company */}
        {!submitted ? (
          <div className="mb-6 p-4 bg-amber-50 border-2 border-amber-300 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-amber-900">Ready to open a title order?</h3>
                <p className="text-sm text-amber-700">Fill out buyer, seller, and lender details to submit</p>
              </div>
              <button onClick={() => setShowOrderForm(true)}
                className="px-6 py-3 bg-amber-600 text-white font-bold rounded-lg hover:bg-amber-700 shadow-md text-sm whitespace-nowrap">
                Submit Title Order
              </button>
            </div>
          </div>
        ) : (
          <div className="mb-6 p-4 bg-emerald-50 border-2 border-emerald-300 rounded-lg">
            <div className="flex items-center gap-3">
              <span className="text-3xl">&#10003;</span>
              <div>
                <h3 className="font-bold text-emerald-900">Title Order Submitted!</h3>
                <p className="text-sm text-emerald-700">Order #{submitted.id} &mdash; Status: {submitted.status || 'submitted'}</p>
                <p className="text-xs text-emerald-600 mt-1">HUB City Title will process your order. Check the Orders tab for updates.</p>
              </div>
            </div>
          </div>
        )}

        {/* Share / PDF / Email / Edit / Sign buttons */}
        <div className="flex flex-wrap gap-3">
          <button onClick={() => navigate('/calculators', { state: { prefill: sheet.input_data, sheetType: sheet.sheet_type } })}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium text-sm">Edit & Recalculate</button>
          <button onClick={handleShare} className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm">Share with Client</button>
          <button onClick={handlePdf} disabled={downloading} className="flex items-center gap-2 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium text-sm">
            {downloading ? 'Generating...' : 'Download PDF'}
          </button>
          <button onClick={() => { const mailto = `mailto:?subject=Net Sheet - ${sheet.property_address || 'Property'}&body=View your net sheet here: ${shareUrl || 'Please click Share first to generate a link'}`; window.open(mailto); }}
            className="flex items-center gap-2 px-4 py-2.5 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium text-sm">Email to Client</button>
          {!isSigned ? (
            <button onClick={() => setShowSignature(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium text-sm">Get Signature</button>
          ) : (
            <span className="flex items-center gap-2 px-4 py-2.5 bg-emerald-100 text-emerald-800 rounded-lg text-sm font-medium">Signed &#10003;</span>
          )}
        </div>

        {shareUrl && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 font-medium">Share link copied to clipboard!</p>
            <a href={shareUrl} target="_blank" rel="noreferrer" className="text-xs text-blue-600 underline break-all">{shareUrl}</a>
          </div>
        )}
      </div>

      {/* Order Form Modal */}
      {showOrderForm && (
        <OrderFormModal
          sheet={sheet}
          onClose={() => setShowOrderForm(false)}
          onSuccess={(order) => { setShowOrderForm(false); setSubmitted(order); }}
        />
      )}

      {/* Full-screen signature pad */}
      {showSignature && (
        <FullScreenSignature
          sheet={sheet}
          onClose={() => setShowSignature(false)}
          onSigned={() => setIsSigned(true)}
        />
      )}
    </div>
  );
}

// -- Saved Sheets List --
export default function SavedSheetPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const incomingSheet = (location.state as any)?.viewSheet || null;
  const [viewing, setViewing] = useState<any>(incomingSheet);

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
          <p className="text-4xl mb-3">&#128221;</p>
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
                        <button onClick={() => setViewing(s)} className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200" title="View">View</button>
                        <button onClick={() => navigate('/calculators', { state: { prefill: s.input_data, sheetType: s.sheet_type } })} className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded hover:bg-amber-200" title="Edit">Edit</button>
                        <button onClick={() => { if (confirm('Delete this sheet?')) deleteMutation.mutate(s.id); }} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200" title="Delete">Delete</button>
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
