import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { api } from '../lib/api';

const CALCS = [
  { slug: 'seller-net-sheet', name: 'Seller Net Sheet', icon: '🏠', desc: 'Calculate seller net proceeds', color: 'bg-emerald-50 border-emerald-200 hover:bg-emerald-100' },
  { slug: 'buyer-estimate', name: 'Buyer Estimate', icon: '🔑', desc: 'Estimate buyer closing costs', color: 'bg-blue-50 border-blue-200 hover:bg-blue-100' },
  { slug: 'truvalue', name: 'TruValue Analysis', icon: '💎', desc: 'Compare net at 3 listing prices', color: 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100' },
  { slug: 'scenario-compare', name: 'Scenario Compare', icon: '🔄', desc: 'Side-by-side offer comparison', color: 'bg-pink-50 border-pink-200 hover:bg-pink-100' },
  { slug: 'buyer-compensation', name: 'Buyer Compensation', icon: '🤝', desc: 'Post-NAR compensation scenarios', color: 'bg-rose-50 border-rose-200 hover:bg-rose-100' },
  { slug: 'buy-now-vs-later', name: 'Buy Now vs Later', icon: '⏳', desc: 'Cost of waiting to purchase', color: 'bg-amber-50 border-amber-200 hover:bg-amber-100' },
  { slug: 'price-vs-rate', name: 'Price vs Rate', icon: '📈', desc: 'Price and rate impact matrix', color: 'bg-cyan-50 border-cyan-200 hover:bg-cyan-100' },
  { slug: 'extra-payment', name: 'Extra Payment', icon: '💰', desc: 'Impact of extra mortgage payments', color: 'bg-lime-50 border-lime-200 hover:bg-lime-100' },
  { slug: 'sell-vs-rent', name: 'Sell vs Rent', icon: '⚖️', desc: 'Compare selling vs renting out', color: 'bg-purple-50 border-purple-200 hover:bg-purple-100' },
  { slug: 'holding-cost', name: 'Holding Cost', icon: '📊', desc: 'Monthly and total holding costs', color: 'bg-orange-50 border-orange-200 hover:bg-orange-100' },
  { slug: 'buydown', name: 'Buydown', icon: '📉', desc: 'Rate buydown break-even', color: 'bg-teal-50 border-teal-200 hover:bg-teal-100' },
];

const fmt = (v: any) => { if (v == null) return '$0.00'; const n = typeof v === 'string' ? parseFloat(v) : v; return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n); };
const pct = (v: any) => { if (v == null) return '0%'; return parseFloat(v).toFixed(2) + '%'; };

const DONUT_COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1'];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>{children}</div>;
}
function Inp({ value, onChange, placeholder, type = 'number', prefix, suffix, ...rest }: any) {
  return (
    <div className="relative">
      {prefix && <span className="absolute left-3 top-2 text-gray-500 text-sm">{prefix}</span>}
      <input type={type} value={value} onChange={(e: any) => onChange(e.target.value)} placeholder={placeholder}
        className={`w-full ${prefix ? 'pl-7' : 'pl-3'} ${suffix ? 'pr-8' : 'pr-3'} py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm`} {...rest} />
      {suffix && <span className="absolute right-3 top-2 text-gray-500 text-sm">{suffix}</span>}
    </div>
  );
}
function Section({ title }: { title: string }) {
  return <h3 className="font-semibold text-gray-700 border-b pb-1 text-sm uppercase tracking-wide pt-2">{title}</h3>;
}
function CalcBtn({ onClick, loading, label }: { onClick: () => void; loading: boolean; label: string }) {
  return <button onClick={onClick} disabled={loading} className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-md hover:bg-indigo-700 transition-colors mt-2">{loading ? 'Calculating...' : label}</button>;
}
function ErrMsg({ error }: { error: string }) {
  return error ? <p className="text-red-600 text-sm mt-1">{error}</p> : null;
}
function Header({ icon, name, desc, onBack }: { icon: string; name: string; desc: string; onBack: () => void }) {
  return (
    <div className="flex justify-between items-center mb-6">
      <div><h2 className="text-xl font-bold text-gray-900">{icon} {name}</h2><p className="text-sm text-gray-500">{desc}</p></div>
      <button onClick={onBack} className="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
    </div>
  );
}
function Placeholder() {
  return (
    <div className="bg-gray-50 border rounded-lg p-12 text-center h-full flex flex-col items-center justify-center">
      <p className="text-5xl mb-4">📋</p>
      <p className="text-gray-500">Fill in the details and click Calculate</p>
      <p className="text-gray-400 text-sm mt-1">Results will appear here</p>
    </div>
  );
}

function OrderFormModal({ sheet, onClose, onSuccess }: { sheet: any; onClose: () => void; onSuccess: (order: any) => void }) {
  const inp = sheet.input_data || {};
  const out = sheet.output_data || {};
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    buyer_name: sheet.sheet_type === 'buyer' ? (sheet.client_name || inp.client_name || '') : '',
    buyer_email: '', buyer_phone: '',
    seller_name: sheet.sheet_type === 'seller' ? (sheet.client_name || inp.client_name || '') : '',
    seller_email: '', seller_phone: '',
    lender_name: '', loan_officer_name: '', escrow_officer_preference: '',
    property_address: sheet.property_address || inp.property_address || '',
    contract_date: '', estimated_closing_date: inp.closing_date || '',
    notes: '',
  });
  const upd = (k: string, v: string) => setForm(p => ({ ...p, [k]: v }));
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setSubmitting(true); setError(null);
    try {
      const res = await api.post('/orders/', { ...form, saved_sheet_id: sheet.id, order_type: 'purchase', status: 'submitted', contract_date: form.contract_date || null, estimated_closing_date: form.estimated_closing_date || null });
      onSuccess(res.data);
    } catch (e: any) { setError(e.response?.data?.detail || 'Submission failed'); }
    setSubmitting(false);
  };
  const fi = (label: string, field: string, type = 'text', ph = '') => (
    <div><label className="block text-xs text-gray-500 mb-1">{label}</label>
    <input type={type} value={(form as any)[field]} onChange={e => upd(field, e.target.value)} placeholder={ph}
      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
  );
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-xl">
          <h2 className="text-lg font-bold text-gray-900">Submit Title Order</h2>
          <p className="text-sm text-gray-500">Complete the details below to submit to HUB City Title</p>
        </div>
        <form onSubmit={submit} className="p-6 space-y-5">
          <div><h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">Property</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="md:col-span-2">{fi('Property Address', 'property_address')}</div>
              {fi('Contract Date', 'contract_date', 'date')}{fi('Est. Closing Date', 'estimated_closing_date', 'date')}
            </div></div>
          <div><h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">Seller</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">{fi('Name', 'seller_name', 'text', 'Jane Doe')}{fi('Email', 'seller_email', 'email', 'jane@email.com')}{fi('Phone', 'seller_phone', 'tel', '(806) 555-1234')}</div></div>
          <div><h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">Buyer</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">{fi('Name', 'buyer_name', 'text', 'John Smith')}{fi('Email', 'buyer_email', 'email', 'john@email.com')}{fi('Phone', 'buyer_phone', 'tel', '(806) 555-5678')}</div></div>
          <div><h3 className="text-sm font-semibold text-gray-700 uppercase mb-2">Lender</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">{fi('Lender Name', 'lender_name', 'text', 'First National Bank')}{fi('Loan Officer', 'loan_officer_name', 'text', 'Mike Johnson')}{fi('Escrow Preference', 'escrow_officer_preference')}</div></div>
          <div><label className="block text-xs text-gray-500 mb-1">Notes</label>
            <textarea value={form.notes} onChange={e => upd('notes', e.target.value)} rows={2} placeholder="Any special instructions..." className="w-full px-3 py-2 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500" /></div>
          {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2.5 text-sm text-gray-700 border rounded-lg hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={submitting} className="px-6 py-2.5 bg-amber-600 text-white font-bold rounded-lg hover:bg-amber-700 shadow-md text-sm disabled:opacity-50">{submitting ? 'Submitting...' : 'Submit Title Order'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SignaturePadFullScreen({ sheet, onClose, onSigned }: { sheet: any; onClose: () => void; onSigned: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [drawing, setDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);
  const [signerName, setSignerName] = useState(sheet.client_name || '');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    const dpr = window.devicePixelRatio || 1; const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr); ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  }, []);
  const getPos = (e: React.MouseEvent | React.TouchEvent) => { const r = canvasRef.current!.getBoundingClientRect(); if ('touches' in e) return { x: e.touches[0].clientX - r.left, y: e.touches[0].clientY - r.top }; return { x: (e as React.MouseEvent).clientX - r.left, y: (e as React.MouseEvent).clientY - r.top }; };
  const start = (e: React.MouseEvent | React.TouchEvent) => { e.preventDefault(); const ctx = canvasRef.current?.getContext('2d'); if (!ctx) return; const p = getPos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); setDrawing(true); setHasDrawn(true); };
  const draw = (e: React.MouseEvent | React.TouchEvent) => { if (!drawing) return; e.preventDefault(); const ctx = canvasRef.current?.getContext('2d'); if (!ctx) return; const p = getPos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); };
  const stop = () => setDrawing(false);
  const clear = () => { const c = canvasRef.current; if (!c) return; c.getContext('2d')?.clearRect(0, 0, c.width, c.height); setHasDrawn(false); };
  const submit = async () => {
    if (!canvasRef.current || !hasDrawn) return; setSubmitting(true);
    try { await api.post(`/saved_sheets/${sheet.id}/sign`, { signature: canvasRef.current.toDataURL('image/png'), signer_name: signerName }); setDone(true); setTimeout(() => { onSigned(); onClose(); }, 2000); }
    catch (e: any) { alert(e.response?.data?.detail || 'Signature failed'); } setSubmitting(false);
  };
  if (done) return (<div className="fixed inset-0 z-50 bg-white flex flex-col items-center justify-center"><div className="text-6xl mb-4">&#9989;</div><h2 className="text-2xl font-bold text-emerald-800">Signed Successfully</h2><p className="text-gray-500 mt-2">Thank you, {signerName || 'Client'}!</p></div>);
  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      <div className="bg-slate-800 text-white px-6 py-4 flex items-center justify-between shrink-0"><div><h2 className="text-lg font-bold">Client Signature</h2><p className="text-sm text-slate-300">{sheet.property_address || 'Net Sheet'}</p></div><button onClick={onClose} className="text-slate-300 hover:text-white text-2xl px-2">&times;</button></div>
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-4 max-w-lg mx-auto w-full">
        <p className="text-gray-600 text-center mb-4">By signing below, I acknowledge that I have reviewed the {sheet.sheet_type === 'seller' ? 'seller net sheet' : 'buyer estimate'} and understand that figures shown are estimates.</p>
        <div className="w-full mb-4"><label className="block text-sm text-gray-500 mb-1">Your Name</label><input type="text" value={signerName} onChange={e => setSignerName(e.target.value)} placeholder="Full Name" className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg text-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
        <div className="w-full border-2 border-gray-300 rounded-lg bg-gray-50 relative mb-4" style={{ touchAction: 'none' }}><canvas ref={canvasRef} className="w-full cursor-crosshair" style={{ height: '200px' }} onMouseDown={start} onMouseMove={draw} onMouseUp={stop} onMouseLeave={stop} onTouchStart={start} onTouchMove={draw} onTouchEnd={stop} /><div className="absolute bottom-3 left-4 right-4 border-b border-gray-400" /><span className="absolute bottom-1 left-4 text-xs text-gray-400">Sign here</span></div>
        <div className="w-full flex gap-3"><button onClick={clear} className="flex-1 py-3 text-gray-700 border-2 border-gray-300 rounded-lg text-base font-medium hover:bg-gray-50">Clear</button><button onClick={submit} disabled={!hasDrawn || submitting} className="flex-[2] py-3 bg-emerald-600 text-white rounded-lg text-base font-bold hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed">{submitting ? 'Saving...' : 'Confirm Signature'}</button></div>
      </div>
    </div>
  );
}

function ActionBar({ result, inputData, sheetType, onBack }: { result: any; inputData: any; sheetType: string; onBack: () => void }) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<any>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [orderSubmitted, setOrderSubmitted] = useState<any>(null);
  const [showSignature, setShowSignature] = useState(false);
  const [isSigned, setIsSigned] = useState(false);
  const handleSave = async () => {
    setSaving(true);
    try { const res = await api.post('/saved_sheets/', { sheet_type: sheetType, property_address: inputData.property_address || '', client_name: inputData.client_name || '', county_id: inputData.county_id ? parseInt(inputData.county_id) : null, input_data: inputData, output_data: result }); setSaved(res.data); } catch (e: any) { console.error('Save error', e); }
    setSaving(false);
  };
  const handleShare = async () => {
    if (!saved?.id) return;
    try {
      const res = await api.post(`/saved_sheets/${saved.id}/share`);
      const url = `${window.location.origin}/shared/${res.data.share_token}`;
      setShareUrl(url);
      const canShare = typeof navigator !== 'undefined' && 'share' in navigator;
      if (canShare) {
        await navigator.share({ title: `${sheetType === 'seller' ? 'Seller Net Sheet' : 'Buyer Estimate'} - ${inputData.property_address || 'Property'}`, text: `View your ${sheetType === 'seller' ? 'seller net sheet' : 'buyer estimate'} from HUB City Title`, url });
      } else {
        await navigator.clipboard.writeText(url);
      }
    } catch (e: any) { if (e.name !== 'AbortError') { try { if (shareUrl) await navigator.clipboard.writeText(shareUrl); } catch {} } }
  };
  const handlePdf = async () => {
    if (!saved?.id) return;
    setDownloading(true);
    try { const res = await api.get(`/saved_sheets_export/${saved.id}/pdf`, { responseType: 'blob' }); const blob = new Blob([res.data], { type: 'application/pdf' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${sheetType}_${saved.id}.pdf`; a.click(); URL.revokeObjectURL(url); } catch (e) { console.error('PDF error', e); }
    setDownloading(false);
  };
  return (
    <div className="mt-4 space-y-2">
      {!saved ? (<button onClick={handleSave} disabled={saving} className="w-full py-2 bg-gray-800 text-white rounded-md text-sm hover:bg-gray-900">{saving ? 'Saving...' : 'Save Sheet'}</button>
      ) : (
        <>
          {!orderSubmitted ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button onClick={handleShare} className="py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700">Share</button>
              <button onClick={handlePdf} disabled={downloading} className="py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700">{downloading ? '...' : 'PDF'}</button>
              <button onClick={() => setShowOrderForm(true)} className="py-2 bg-amber-600 text-white rounded-md text-sm hover:bg-amber-700 font-semibold">Submit Order</button>
              {!isSigned ? (
                <button onClick={() => setShowSignature(true)} className="py-2 bg-emerald-600 text-white rounded-md text-sm hover:bg-emerald-700 font-semibold">Get Signature</button>
              ) : (
                <span className="py-2 bg-emerald-100 text-emerald-800 rounded-md text-sm text-center font-medium">Signed &#10003;</span>
              )}
            </div>
          ) : (
            <div className="p-3 bg-emerald-50 border-2 border-emerald-300 rounded-lg">
              <p className="font-bold text-emerald-900 text-sm">Order #{orderSubmitted.id} Submitted!</p>
              <p className="text-xs text-emerald-700">Check the Orders tab for updates.</p>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <button onClick={handleShare} className="py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700">Share</button>
                <button onClick={handlePdf} disabled={downloading} className="py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700">{downloading ? '...' : 'PDF'}</button>
              </div>
            </div>
          )}
        </>
      )}
      {shareUrl && (<div className="w-full p-3 bg-blue-50 border border-blue-200 rounded-md"><p className="text-sm text-blue-800 font-medium">Share link ready!</p><a href={shareUrl} target="_blank" rel="noreferrer" className="text-xs text-blue-600 underline break-all">{shareUrl}</a></div>)}
      {showOrderForm && saved && <OrderFormModal sheet={{ ...saved, input_data: inputData, output_data: result, sheet_type: sheetType }} onClose={() => setShowOrderForm(false)} onSuccess={(order) => { setShowOrderForm(false); setOrderSubmitted(order); }} />}
      {showSignature && saved && <SignaturePadFullScreen sheet={{ ...saved, input_data: inputData, output_data: result, sheet_type: sheetType, property_address: inputData.property_address || '', client_name: inputData.client_name || '' }} onClose={() => setShowSignature(false)} onSigned={() => setIsSigned(true)} />}
    </div>
  );
}

function ShareOnlyBar({ result, inputData, sheetType }: { result: any; inputData: any; sheetType: string }) {
  const [copied, setCopied] = useState(false);
  const calcName = CALCS.find(c => c.slug === sheetType)?.name || sheetType;
  const buildShareText = () => {
    let text = `${calcName} Results\n`;
    if (inputData.property_address) text += `Property: ${inputData.property_address}\n`;
    text += `\n`;
    if (result.line_items?.length) {
      result.line_items.forEach((item: any) => { text += `${item.label}: ${fmt(item.amount)}\n`; });
      text += `\n`;
    }
    if (result.net_proceeds != null) text += `Net Proceeds: ${fmt(result.net_proceeds)}\n`;
    if (result.cash_to_close != null) text += `Cash to Close: ${fmt(result.cash_to_close)}\n`;
    if (result.total_monthly_cost != null) text += `Total Monthly Cost: ${fmt(result.total_monthly_cost)}\n`;
    if (result.total_holding_cost != null) text += `Total Holding Cost: ${fmt(result.total_holding_cost)}\n`;
    if (result.recommendation) text += `\n${result.recommendation}\n`;
    text += `\nPowered by HUB City Title`;
    return text;
  };
  const handleShare = async () => {
    const text = buildShareText();
    const canShare = typeof navigator !== 'undefined' && 'share' in navigator;
    if (canShare) {
      try { await navigator.share({ title: `${calcName} - HUB City Title`, text }); return; } catch (e: any) { if (e.name === 'AbortError') return; }
    }
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 3000); } catch {}
  };
  return (
    <div className="mt-4">
      <button onClick={handleShare} className="w-full py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 font-medium">
        {copied ? 'Copied to Clipboard!' : 'Share Results'}
      </button>
    </div>
  );
}

function ResultPanel({ result, title }: { result: any; title: string }) {
  // Build donut data from line_items
  const donutData = (result.line_items || []).filter((item: any) => item.amount > 0).map((item: any, i: number) => ({
    name: item.label, value: Math.abs(parseFloat(item.amount) || 0), color: DONUT_COLORS[i % DONUT_COLORS.length]
  }));
  const mainValue = result.net_proceeds ?? result.cash_to_close;
  const mainLabel = result.net_proceeds != null ? 'Net Proceeds' : result.cash_to_close != null ? 'Cash to Close' : '';
  const mainColor = result.net_proceeds != null ? 'text-emerald-600' : 'text-blue-600';

  return (
    <div className="bg-gray-50 p-6 rounded-lg border">
      <h3 className="font-semibold text-gray-700 mb-4">{title}</h3>

      {/* Donut Chart */}
      {mainValue != null && donutData.length > 0 && (
        <div className="mb-4">
          <div className="relative">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={donutData} cx="50%" cy="50%" innerRadius={65} outerRadius={95} paddingAngle={2} dataKey="value" stroke="none">
                  {donutData.map((d: any, i: number) => <Cell key={i} fill={d.color} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <p className="text-xs text-gray-500 uppercase tracking-wide">{mainLabel}</p>
              <p className={`text-2xl font-bold ${mainColor}`}>{fmt(mainValue)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Fallback big number if no donut */}
      {mainValue != null && donutData.length === 0 && (
        <div className="text-center mb-4 p-4 bg-white rounded-lg border">
          <p className="text-xs text-gray-500 uppercase tracking-wide">{mainLabel}</p>
          <p className={`text-3xl font-bold ${mainColor}`}>{fmt(mainValue)}</p>
        </div>
      )}

      {/* Legend / Line Items */}
      {donutData.length > 0 ? (
        <div className="space-y-1">
          {donutData.map((d: any, i: number) => (
            <div key={i} className="flex items-center justify-between text-sm py-1 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: d.color }} />
                <span className="text-gray-700">{d.name}</span>
              </div>
              <span className="font-medium">{fmt(d.value)}</span>
            </div>
          ))}
        </div>
      ) : result.line_items?.length > 0 ? (
        <div className="space-y-0.5">{result.line_items.map((item: any, i: number) => (
          <div key={i} className="flex justify-between text-sm py-1.5 border-b border-gray-200"><span className="text-gray-700">{item.label}</span><span className="font-medium">{fmt(item.amount)}</span></div>
        ))}</div>
      ) : null}

      <div className="mt-4 pt-3 border-t-2 border-gray-300 space-y-1">
        {result.sale_price != null && <div className="flex justify-between text-sm"><span>Sale Price</span><span className="font-semibold">{fmt(result.sale_price)}</span></div>}
        {result.purchase_price != null && <div className="flex justify-between text-sm"><span>Purchase Price</span><span className="font-semibold">{fmt(result.purchase_price)}</span></div>}
        {result.total_closing_costs != null && <div className="flex justify-between text-sm"><span>Total Closing Costs</span><span className="font-semibold text-red-600">-{fmt(result.total_closing_costs)}</span></div>}
      </div>
    </div>
  );
}

// ── 1. SELLER NET SHEET ──
function SellerForm({ counties, onBack, prefill }: { counties: any[]; onBack: () => void; prefill?: any }) {
  const { data: taxDistricts } = useQuery({ queryKey: ['tax-districts'], queryFn: () => api.get('/tax_districts/').then(r => r.data) });
  const allDistricts = taxDistricts || [];
  const defaults = { sale_price: '350000', existing_loan_balance: '150000', seller_agent_commission_pct: '3.0', buyer_agent_commission_pct: '3.0', county_id: counties[0]?.id?.toString() || '1', closing_date: '2026-07-15', prior_title_insurance: false, years_since_prior_policy: '0', hoa_payoff: '0', seller_concessions: '0', include_home_warranty: true, include_survey: false, miscellaneous_fees: '0', annual_property_taxes: '0', property_address: '', client_name: '', tax_district_id: '', home_warranty_amount: '700' };
  const [f, sF] = useState(prefill ? { ...defaults, ...Object.fromEntries(Object.entries(prefill).filter(([_, v]) => v !== null && v !== undefined).map(([k, v]) => [k, String(v)])), prior_title_insurance: prefill.prior_title_insurance ?? false, include_home_warranty: prefill.include_home_warranty ?? true, include_survey: prefill.include_survey ?? false } : defaults);
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const districts = allDistricts.filter((d: any) => d.county_id?.toString() === f.county_id?.toString());
  const s = (k: string, v: any) => {
    const next = { ...f, [k]: v };
    // Reset tax district when county changes
    if (k === 'county_id') { next.tax_district_id = ''; next.annual_property_taxes = '0'; }
    // Auto-calc taxes when district or sale price changes
    if (k === 'tax_district_id' || k === 'sale_price') {
      const distId = k === 'tax_district_id' ? v : next.tax_district_id;
      const price = k === 'sale_price' ? parseFloat(v) : parseFloat(next.sale_price);
      if (distId && distId !== 'custom') {
        const dist = districts.find((d: any) => d.id.toString() === distId.toString());
        if (dist && !isNaN(price)) {
          next.annual_property_taxes = (price * parseFloat(dist.combined_rate_pct) / 100).toFixed(2);
        }
      }
    }
    sF(next);
  };
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/seller-net-sheet', { ...f, sale_price: parseFloat(f.sale_price), existing_loan_balance: parseFloat(f.existing_loan_balance), seller_agent_commission_pct: parseFloat(f.seller_agent_commission_pct), buyer_agent_commission_pct: parseFloat(f.buyer_agent_commission_pct), county_id: parseInt(f.county_id), hoa_payoff: parseFloat(f.hoa_payoff), seller_concessions: parseFloat(f.seller_concessions), miscellaneous_fees: parseFloat(f.miscellaneous_fees), annual_property_taxes: parseFloat(f.annual_property_taxes), home_warranty_amount: parseFloat(f.home_warranty_amount), years_since_prior_policy: f.prior_title_insurance ? parseInt(f.years_since_prior_policy) : null }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="🏠" name="Seller Net Sheet" desc="Calculate estimated net proceeds for seller" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Section title="Property Info" />
          <Field label="Property Address"><Inp type="text" value={f.property_address} onChange={(v: string) => s('property_address', v)} placeholder="123 Main St" /></Field>
          <Field label="Client / Seller Name"><Inp type="text" value={f.client_name} onChange={(v: string) => s('client_name', v)} placeholder="John Smith" /></Field>
          <Field label="County"><select value={f.county_id} onChange={e => s('county_id', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">{counties.map((c: any) => <option key={c.id} value={c.id}>{c.county_name}, {c.state}</option>)}</select></Field>
          <Field label="Closing Date"><Inp type="date" value={f.closing_date} onChange={(v: string) => s('closing_date', v)} /></Field>
          <Section title="Price & Loan" />
          <Field label="Sale Price"><Inp value={f.sale_price} onChange={(v: string) => s('sale_price', v)} prefix="$" /></Field>
          <Field label="Existing Loan Balance"><Inp value={f.existing_loan_balance} onChange={(v: string) => s('existing_loan_balance', v)} prefix="$" /></Field>
          <Section title="Commissions" />
          <div className="grid grid-cols-2 gap-3"><Field label="Seller Agent"><Inp value={f.seller_agent_commission_pct} onChange={(v: string) => s('seller_agent_commission_pct', v)} suffix="%" /></Field><Field label="Buyer Agent"><Inp value={f.buyer_agent_commission_pct} onChange={(v: string) => s('buyer_agent_commission_pct', v)} suffix="%" /></Field></div>
          <Section title="Tax & Options" />
          <Field label="Tax District">
            <select value={f.tax_district_id} onChange={e => s('tax_district_id', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="custom">Custom (enter manually)</option>
              {districts.map((d: any) => <option key={d.id} value={d.id}>{d.name} — {parseFloat(d.combined_rate_pct).toFixed(2)}%</option>)}
            </select>
          </Field>
          <Field label="Annual Property Taxes">
            <div className="relative">
              <Inp value={f.annual_property_taxes} onChange={(v: string) => { sF(p => ({ ...p, annual_property_taxes: v, tax_district_id: 'custom' })); }} prefix="$" />
              {f.tax_district_id && f.tax_district_id !== 'custom' && (
                <span className="absolute right-3 top-2 text-xs text-emerald-600 font-medium">auto</span>
              )}
            </div>
          </Field>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.include_home_warranty} onChange={e => s('include_home_warranty', e.target.checked)} /> Include Home Warranty</label>
            {f.include_home_warranty && <Field label="Home Warranty Amount"><Inp value={f.home_warranty_amount} onChange={(v: string) => s('home_warranty_amount', v)} prefix="$" /></Field>}
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.include_survey} onChange={e => s('include_survey', e.target.checked)} /> Include Survey</label>
          </div>
          <Section title="Other Costs" />
          <div className="grid grid-cols-2 gap-3"><Field label="HOA Payoff"><Inp value={f.hoa_payoff} onChange={(v: string) => s('hoa_payoff', v)} prefix="$" /></Field><Field label="Seller Concessions"><Inp value={f.seller_concessions} onChange={(v: string) => s('seller_concessions', v)} prefix="$" /></Field></div>
          <Field label="Misc Fees"><Inp value={f.miscellaneous_fees} onChange={(v: string) => s('miscellaneous_fees', v)} prefix="$" /></Field>
          <CalcBtn onClick={calc} loading={loading} label="Calculate Net Proceeds" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<><ResultPanel result={result} title="Seller Net Sheet Results" /><ActionBar result={result} inputData={f} sheetType="seller" onBack={() => setResult(null)} /></>) : <Placeholder />}</div>
      </div>
    </div>
  );
}

// ── 2. BUYER ESTIMATE ──
function BuyerForm({ counties, onBack, prefill }: { counties: any[]; onBack: () => void; prefill?: any }) {
  const { data: taxDistricts } = useQuery({ queryKey: ['tax-districts'], queryFn: () => api.get('/tax_districts/').then(r => r.data) });
  const allDistricts = taxDistricts || [];
  const defaults = { purchase_price: '350000', loan_amount: '280000', loan_type: 'conventional', interest_rate: '6.75', county_id: counties[0]?.id?.toString() || '1', closing_date: '2026-07-15', annual_property_taxes: '0', annual_homeowners_insurance: '2850', months_insurance_prepaid: '14', months_tax_escrow: '4', seller_paid_closing_costs: '0', property_address: '', client_name: '', tax_district_id: '', misc_lender_fees: '1100', appraisal_fee: '450', credit_report_fee: '40', survey_fee: '500', pest_inspection_fee: '100', home_inspection_fee: '400', escrow_fee: '250', doc_prep_buyer: '225', t19_endorsement: '80.99', survey_cover_endorsement: '99.15', t17_endorsement: '25', t36_endorsement: '25', t30_endorsement: '25' };
  const [f, sF] = useState(prefill ? { ...defaults, ...Object.fromEntries(Object.entries(prefill).filter(([_, v]) => v !== null && v !== undefined).map(([k, v]) => [k, String(v)])) } : defaults);
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const districts = allDistricts.filter((d: any) => d.county_id?.toString() === f.county_id?.toString());
  const s = (k: string, v: any) => {
    const next = { ...f, [k]: v };
    if (k === 'county_id') { next.tax_district_id = ''; next.annual_property_taxes = '0'; }
    if (k === 'tax_district_id' || k === 'purchase_price') {
      const distId = k === 'tax_district_id' ? v : next.tax_district_id;
      const price = k === 'purchase_price' ? parseFloat(v) : parseFloat(next.purchase_price);
      if (distId && distId !== 'custom') {
        const dist = districts.find((d: any) => d.id.toString() === distId.toString());
        if (dist && !isNaN(price)) {
          next.annual_property_taxes = (price * parseFloat(dist.combined_rate_pct) / 100).toFixed(2);
        }
      }
    }
    sF(next);
  };
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/buyer-estimate', { ...f, purchase_price: parseFloat(f.purchase_price), loan_amount: parseFloat(f.loan_amount), interest_rate: parseFloat(f.interest_rate), county_id: parseInt(f.county_id), annual_property_taxes: parseFloat(f.annual_property_taxes), annual_homeowners_insurance: parseFloat(f.annual_homeowners_insurance), months_insurance_prepaid: parseInt(f.months_insurance_prepaid), months_tax_escrow: parseInt(f.months_tax_escrow), seller_paid_closing_costs: parseFloat(f.seller_paid_closing_costs), misc_lender_fees: parseFloat(f.misc_lender_fees), appraisal_fee: parseFloat(f.appraisal_fee), credit_report_fee: parseFloat(f.credit_report_fee), survey_fee: parseFloat(f.survey_fee), pest_inspection_fee: parseFloat(f.pest_inspection_fee), home_inspection_fee: parseFloat(f.home_inspection_fee), escrow_fee: parseFloat(f.escrow_fee), doc_prep_buyer: parseFloat(f.doc_prep_buyer), t19_endorsement: parseFloat(f.t19_endorsement), survey_cover_endorsement: parseFloat(f.survey_cover_endorsement), t17_endorsement: parseFloat(f.t17_endorsement), t36_endorsement: parseFloat(f.t36_endorsement), t30_endorsement: parseFloat(f.t30_endorsement) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="🔑" name="Buyer Estimate" desc="Estimate buyer closing costs" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Section title="Property Info" />
          <Field label="Property Address"><Inp type="text" value={f.property_address} onChange={(v: string) => s('property_address', v)} placeholder="123 Main St" /></Field>
          <Field label="Client / Buyer Name"><Inp type="text" value={f.client_name} onChange={(v: string) => s('client_name', v)} placeholder="Jane Smith" /></Field>
          <Field label="County"><select value={f.county_id} onChange={e => s('county_id', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">{counties.map((c: any) => <option key={c.id} value={c.id}>{c.county_name}, {c.state}</option>)}</select></Field>
          <Field label="Closing Date"><Inp type="date" value={f.closing_date} onChange={(v: string) => s('closing_date', v)} /></Field>
          <Section title="Purchase & Loan" />
          <Field label="Purchase Price"><Inp value={f.purchase_price} onChange={(v: string) => s('purchase_price', v)} prefix="$" /></Field>
          <Field label="Loan Amount"><Inp value={f.loan_amount} onChange={(v: string) => s('loan_amount', v)} prefix="$" /></Field>
          <Field label="Loan Type"><select value={f.loan_type} onChange={e => s('loan_type', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"><option value="conventional">Conventional</option><option value="fha">FHA</option><option value="va">VA</option><option value="usda">USDA</option></select></Field>
          <Field label="Interest Rate"><Inp value={f.interest_rate} onChange={(v: string) => s('interest_rate', v)} suffix="%" /></Field>
          <Section title="Tax & Insurance" />
          <Field label="Tax District">
            <select value={f.tax_district_id} onChange={e => s('tax_district_id', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="custom">Custom (enter manually)</option>
              {districts.map((d: any) => <option key={d.id} value={d.id}>{d.name} — {parseFloat(d.combined_rate_pct).toFixed(2)}%</option>)}
            </select>
          </Field>
          <Field label="Annual Property Taxes">
            <div className="relative">
              <Inp value={f.annual_property_taxes} onChange={(v: string) => { sF(p => ({ ...p, annual_property_taxes: v, tax_district_id: 'custom' })); }} prefix="$" />
              {f.tax_district_id && f.tax_district_id !== 'custom' && (
                <span className="absolute right-3 top-2 text-xs text-emerald-600 font-medium">auto</span>
              )}
            </div>
          </Field>
          <Field label="Annual Homeowners Insurance"><Inp value={f.annual_homeowners_insurance} onChange={(v: string) => s('annual_homeowners_insurance', v)} prefix="$" /></Field>
          <div className="grid grid-cols-2 gap-3"><Field label="Months Insurance Prepaid"><Inp value={f.months_insurance_prepaid} onChange={(v: string) => s('months_insurance_prepaid', v)} /></Field><Field label="Months Tax Escrow"><Inp value={f.months_tax_escrow} onChange={(v: string) => s('months_tax_escrow', v)} /></Field></div>
          <Section title="Lender Fees" />
          <div className="grid grid-cols-3 gap-3">
            <Field label="Misc. Lender Fees"><Inp value={f.misc_lender_fees} onChange={(v: string) => s('misc_lender_fees', v)} prefix="$" /></Field>
            <Field label="Appraisal"><Inp value={f.appraisal_fee} onChange={(v: string) => s('appraisal_fee', v)} prefix="$" /></Field>
            <Field label="Credit Report"><Inp value={f.credit_report_fee} onChange={(v: string) => s('credit_report_fee', v)} prefix="$" /></Field>
          </div>
          <Section title="Inspections" />
          <div className="grid grid-cols-3 gap-3">
            <Field label="Survey"><Inp value={f.survey_fee} onChange={(v: string) => s('survey_fee', v)} prefix="$" /></Field>
            <Field label="Pest Inspection"><Inp value={f.pest_inspection_fee} onChange={(v: string) => s('pest_inspection_fee', v)} prefix="$" /></Field>
            <Field label="Home Inspection"><Inp value={f.home_inspection_fee} onChange={(v: string) => s('home_inspection_fee', v)} prefix="$" /></Field>
          </div>
          <Section title="Title Endorsements" />
          <div className="grid grid-cols-2 gap-3">
            <Field label="T-19 Endorsement"><Inp value={f.t19_endorsement} onChange={(v: string) => s('t19_endorsement', v)} prefix="$" /></Field>
            <Field label="Survey Cover"><Inp value={f.survey_cover_endorsement} onChange={(v: string) => s('survey_cover_endorsement', v)} prefix="$" /></Field>
            <Field label="T-17 Mortgagee's"><Inp value={f.t17_endorsement} onChange={(v: string) => s('t17_endorsement', v)} prefix="$" /></Field>
            <Field label="T-36 Mortgagee's"><Inp value={f.t36_endorsement} onChange={(v: string) => s('t36_endorsement', v)} prefix="$" /></Field>
            <Field label="T-30 Mortgagee's"><Inp value={f.t30_endorsement} onChange={(v: string) => s('t30_endorsement', v)} prefix="$" /></Field>
          </div>
          <Section title="Credits" />
          <Field label="Seller-Paid Closing Costs"><Inp value={f.seller_paid_closing_costs} onChange={(v: string) => s('seller_paid_closing_costs', v)} prefix="$" /></Field>
          <CalcBtn onClick={calc} loading={loading} label="Calculate Cash to Close" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<>
          {/* Monthly Payment donut */}
          {result.monthly_payment && (
            <div className="bg-gray-50 p-6 rounded-lg border mb-4">
              <h3 className="font-semibold text-gray-700 mb-4">Monthly Payment</h3>
              <div className="relative">
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart><Pie data={[
                    { name: 'P&I', value: parseFloat(result.monthly_pi || 0), color: '#3b82f6' },
                    { name: 'Taxes', value: parseFloat(result.monthly_taxes || 0), color: '#10b981' },
                    { name: 'Insurance', value: parseFloat(result.monthly_insurance || 0), color: '#f59e0b' },
                    ...(result.monthly_pmi ? [{ name: 'PMI', value: parseFloat(result.monthly_pmi), color: '#ef4444' }] : []),
                  ].filter(d => d.value > 0)} cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={2} dataKey="value" stroke="none">
                    {[{ color: '#3b82f6' }, { color: '#10b981' }, { color: '#f59e0b' }, { color: '#ef4444' }].map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie></PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <p className="text-xs text-gray-500">MONTHLY</p>
                  <p className="text-xl font-bold text-gray-900">{fmt(result.monthly_payment)}</p>
                </div>
              </div>
              <div className="space-y-1 mt-2">
                <div className="flex items-center justify-between text-sm"><div className="flex items-center gap-2"><div className="w-3 h-3 rounded-sm bg-blue-500" /><span>P&I</span></div><span className="font-medium">{fmt(result.monthly_pi)}</span></div>
                <div className="flex items-center justify-between text-sm"><div className="flex items-center gap-2"><div className="w-3 h-3 rounded-sm bg-emerald-500" /><span>Taxes</span></div><span className="font-medium">{fmt(result.monthly_taxes)}</span></div>
                <div className="flex items-center justify-between text-sm"><div className="flex items-center gap-2"><div className="w-3 h-3 rounded-sm bg-amber-500" /><span>Insurance</span></div><span className="font-medium">{fmt(result.monthly_insurance)}</span></div>
                {result.monthly_pmi && <div className="flex items-center justify-between text-sm"><div className="flex items-center gap-2"><div className="w-3 h-3 rounded-sm bg-red-500" /><span>PMI</span></div><span className="font-medium">{fmt(result.monthly_pmi)}</span></div>}
              </div>
            </div>
          )}
          <ResultPanel result={result} title="Buyer Estimate Results" />
          <ActionBar result={result} inputData={f} sheetType="buyer" onBack={() => setResult(null)} />
        </>) : <Placeholder />}</div>
      </div>
    </div>
  );
}

// ── 3. TRUVALUE ANALYSIS ──
function TruValueForm({ counties, onBack }: { counties: any[]; onBack: () => void }) {
  const [f, sF] = useState({ county_id: counties[0]?.id?.toString() || '1', existing_loan_balance: '150000', price_low: '300000', price_mid: '325000', price_high: '350000', seller_agent_commission_pct: '3.0', buyer_agent_commission_pct: '3.0', include_home_warranty: true, days_on_market_low: '7', days_on_market_mid: '21', days_on_market_high: '45', monthly_holding_cost: '1500' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/truvalue', { county_id: parseInt(f.county_id), existing_loan_balance: parseFloat(f.existing_loan_balance), price_low: parseFloat(f.price_low), price_mid: parseFloat(f.price_mid), price_high: parseFloat(f.price_high), seller_agent_commission_pct: parseFloat(f.seller_agent_commission_pct), buyer_agent_commission_pct: parseFloat(f.buyer_agent_commission_pct), include_home_warranty: f.include_home_warranty, days_on_market_low: parseInt(f.days_on_market_low), days_on_market_mid: parseInt(f.days_on_market_mid), days_on_market_high: parseInt(f.days_on_market_high), monthly_holding_cost: parseFloat(f.monthly_holding_cost) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="💎" name="TruValue Analysis" desc="Compare net proceeds at 3 listing prices" onBack={onBack} />
      <div className="space-y-3 max-w-2xl">
        <Section title="Loan & County" />
        <div className="grid grid-cols-2 gap-3">
          <Field label="County"><select value={f.county_id} onChange={e => s('county_id', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">{counties.map((c: any) => <option key={c.id} value={c.id}>{c.county_name}, {c.state}</option>)}</select></Field>
          <Field label="Existing Loan Balance"><Inp value={f.existing_loan_balance} onChange={(v: string) => s('existing_loan_balance', v)} prefix="$" /></Field>
        </div>
        <Section title="3 Pricing Scenarios" />
        <div className="grid grid-cols-3 gap-3">
          <Field label="Low Price"><Inp value={f.price_low} onChange={(v: string) => s('price_low', v)} prefix="$" /></Field>
          <Field label="Mid Price"><Inp value={f.price_mid} onChange={(v: string) => s('price_mid', v)} prefix="$" /></Field>
          <Field label="High Price"><Inp value={f.price_high} onChange={(v: string) => s('price_high', v)} prefix="$" /></Field>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Days on Market"><Inp value={f.days_on_market_low} onChange={(v: string) => s('days_on_market_low', v)} /></Field>
          <Field label="Days on Market"><Inp value={f.days_on_market_mid} onChange={(v: string) => s('days_on_market_mid', v)} /></Field>
          <Field label="Days on Market"><Inp value={f.days_on_market_high} onChange={(v: string) => s('days_on_market_high', v)} /></Field>
        </div>
        <Section title="Costs" />
        <div className="grid grid-cols-2 gap-3">
          <Field label="Seller Agent"><Inp value={f.seller_agent_commission_pct} onChange={(v: string) => s('seller_agent_commission_pct', v)} suffix="%" /></Field>
          <Field label="Buyer Agent"><Inp value={f.buyer_agent_commission_pct} onChange={(v: string) => s('buyer_agent_commission_pct', v)} suffix="%" /></Field>
        </div>
        <Field label="Monthly Holding Cost"><Inp value={f.monthly_holding_cost} onChange={(v: string) => s('monthly_holding_cost', v)} prefix="$" /></Field>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.include_home_warranty} onChange={e => s('include_home_warranty', e.target.checked)} /> Include Home Warranty</label>
        <CalcBtn onClick={calc} loading={loading} label="Compare 3 Scenarios" /><ErrMsg error={error} />
      </div>
      {result?.scenarios && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {result.scenarios.map((sc: any, i: number) => (
            <div key={i} className={`p-5 rounded-lg border-2 ${i === 1 ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 bg-gray-50'}`}>
              <p className="text-xs text-gray-500 uppercase font-semibold">{sc.label}</p>
              <p className="text-xl font-bold mt-1">{fmt(sc.list_price)}</p>
              <div className="mt-3 space-y-1 text-sm">
                <div className="flex justify-between"><span>Net Proceeds</span><span className="font-semibold text-emerald-600">{fmt(sc.net_proceeds)}</span></div>
                <div className="flex justify-between"><span>Closing Costs</span><span className="text-red-600">-{fmt(sc.total_closing_costs)}</span></div>
                <div className="flex justify-between"><span>Days on Market</span><span>{sc.days_on_market}</span></div>
                <div className="flex justify-between"><span>Holding Cost</span><span className="text-red-600">-{fmt(sc.holding_cost)}</span></div>
                <div className="flex justify-between border-t pt-1 mt-1"><span className="font-semibold">Adjusted Net</span><span className="font-bold text-lg">{fmt(sc.adjusted_net)}</span></div>
              </div>
            </div>
          ))}
        </div>
      )}
      {result && <ShareOnlyBar result={result} inputData={f} sheetType="truvalue" />}
    </div>
  );
}

// ── 4. SELL VS RENT ──
function SellVsRentForm({ onBack }: { onBack: () => void }) {
  const [f, sF] = useState({ current_value: '350000', monthly_rent_income: '2200', monthly_mortgage_payment: '1800', annual_tax_rate_pct: '2.0', annual_appreciation_rate_pct: '3.0', analysis_years: '5' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/sell-vs-rent', { current_value: parseFloat(f.current_value), monthly_rent_income: parseFloat(f.monthly_rent_income), monthly_mortgage_payment: parseFloat(f.monthly_mortgage_payment), annual_tax_rate_pct: parseFloat(f.annual_tax_rate_pct), annual_appreciation_rate_pct: parseFloat(f.annual_appreciation_rate_pct), analysis_years: parseInt(f.analysis_years) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="⚖️" name="Sell vs Rent" desc="Compare selling now vs renting out the property" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Field label="Current Property Value"><Inp value={f.current_value} onChange={(v: string) => s('current_value', v)} prefix="$" /></Field>
          <Field label="Monthly Rent Income"><Inp value={f.monthly_rent_income} onChange={(v: string) => s('monthly_rent_income', v)} prefix="$" /></Field>
          <Field label="Monthly Mortgage Payment"><Inp value={f.monthly_mortgage_payment} onChange={(v: string) => s('monthly_mortgage_payment', v)} prefix="$" /></Field>
          <Field label="Annual Property Tax Rate"><Inp value={f.annual_tax_rate_pct} onChange={(v: string) => s('annual_tax_rate_pct', v)} suffix="%" /></Field>
          <Field label="Annual Appreciation Rate"><Inp value={f.annual_appreciation_rate_pct} onChange={(v: string) => s('annual_appreciation_rate_pct', v)} suffix="%" /></Field>
          <Field label="Analysis Period (years)"><Inp value={f.analysis_years} onChange={(v: string) => s('analysis_years', v)} /></Field>
          <CalcBtn onClick={calc} loading={loading} label="Analyze Sell vs Rent" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<div className="bg-gray-50 p-6 rounded-lg border">
          {result.break_even_year && <p className="text-sm mb-3 p-3 bg-amber-50 border border-amber-200 rounded">Break-even at year {result.break_even_year}</p>}
          {result.recommendation_text && <p className="text-sm mb-4 p-3 bg-blue-50 border border-blue-200 rounded">{result.recommendation_text}</p>}
          <table className="w-full text-sm"><thead><tr className="border-b"><th className="text-left py-1">Year</th><th className="text-right">If Sell</th><th className="text-right">If Rent</th><th className="text-right">Diff</th></tr></thead><tbody>
            {result.projection?.map((y: any) => (<tr key={y.year} className="border-b"><td className="py-1">{y.year}</td><td className="text-right">{fmt(y.equity_if_sell)}</td><td className="text-right">{fmt(y.net_if_rent)}</td><td className={`text-right font-medium ${parseFloat(y.difference) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{fmt(y.difference)}</td></tr>))}
          </tbody></table>
        </div>) : <Placeholder />}
        {result && <ShareOnlyBar result={result} inputData={f} sheetType="sell-vs-rent" />}
        </div>
      </div>
    </div>
  );
}

// ── 5. HOLDING COST ──
function HoldingCostForm({ onBack }: { onBack: () => void }) {
  const [f, sF] = useState({ purchase_price: '350000', loan_rate_pct: '7.0', months_holding: '6', annual_property_tax: '2930', annual_insurance: '1800', monthly_hoa: '0', monthly_maintenance: '200' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/holding-cost', { purchase_price: parseFloat(f.purchase_price), loan_rate_pct: parseFloat(f.loan_rate_pct), months_holding: parseInt(f.months_holding), annual_property_tax: parseFloat(f.annual_property_tax), annual_insurance: parseFloat(f.annual_insurance), monthly_hoa: parseFloat(f.monthly_hoa), monthly_maintenance: parseFloat(f.monthly_maintenance) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="📊" name="Holding Cost" desc="Calculate total cost of holding a property" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Field label="Property Value"><Inp value={f.purchase_price} onChange={(v: string) => s('purchase_price', v)} prefix="$" /></Field>
          <Field label="Loan Interest Rate"><Inp value={f.loan_rate_pct} onChange={(v: string) => s('loan_rate_pct', v)} suffix="%" /></Field>
          <Field label="Months Holding"><Inp value={f.months_holding} onChange={(v: string) => s('months_holding', v)} /></Field>
          <Field label="Annual Property Tax"><Inp value={f.annual_property_tax} onChange={(v: string) => s('annual_property_tax', v)} prefix="$" /></Field>
          <Field label="Annual Insurance"><Inp value={f.annual_insurance} onChange={(v: string) => s('annual_insurance', v)} prefix="$" /></Field>
          <Field label="Monthly HOA"><Inp value={f.monthly_hoa} onChange={(v: string) => s('monthly_hoa', v)} prefix="$" /></Field>
          <Field label="Monthly Maintenance"><Inp value={f.monthly_maintenance} onChange={(v: string) => s('monthly_maintenance', v)} prefix="$" /></Field>
          <CalcBtn onClick={calc} loading={loading} label="Calculate Holding Costs" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<div className="bg-gray-50 p-6 rounded-lg border">
          <div className="text-center mb-4 p-4 bg-white rounded-lg border"><p className="text-xs text-gray-500 uppercase">Monthly Cost</p><p className="text-3xl font-bold text-orange-600">{fmt(result.monthly_cost)}</p></div>
          <div className="text-center mb-4 p-4 bg-white rounded-lg border"><p className="text-xs text-gray-500 uppercase">Total ({f.months_holding} months)</p><p className="text-3xl font-bold text-red-600">{fmt(result.total_cost)}</p></div>
          {result.line_items?.map((item: any, i: number) => (<div key={i} className="flex justify-between text-sm py-1.5 border-b"><span>{item.label}</span><span className="font-medium">{fmt(item.amount)}</span></div>))}
        </div>) : <Placeholder />}
        {result && <ShareOnlyBar result={result} inputData={f} sheetType="holding-cost" />}
        </div>
      </div>
    </div>
  );
}

// ── 6. BUYDOWN ──
function BuydownForm({ onBack }: { onBack: () => void }) {
  const [f, sF] = useState({ loan_amount: '280000', base_rate_pct: '7.0', buydown_type: '2-1', points_cost: '0', loan_term_years: '30' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/buydown', { loan_amount: parseFloat(f.loan_amount), base_rate_pct: parseFloat(f.base_rate_pct), buydown_type: f.buydown_type, points_cost: parseFloat(f.points_cost), loan_term_years: parseInt(f.loan_term_years) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="📉" name="Rate Buydown" desc="See payment savings from temporary buydowns" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Field label="Loan Amount"><Inp value={f.loan_amount} onChange={(v: string) => s('loan_amount', v)} prefix="$" /></Field>
          <Field label="Base Interest Rate"><Inp value={f.base_rate_pct} onChange={(v: string) => s('base_rate_pct', v)} suffix="%" /></Field>
          <Field label="Buydown Type"><select value={f.buydown_type} onChange={e => s('buydown_type', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"><option value="2-1">2-1 Buydown</option><option value="1-0">1-0 Buydown</option><option value="3-2-1">3-2-1 Buydown</option></select></Field>
          <Field label="Points Cost"><Inp value={f.points_cost} onChange={(v: string) => s('points_cost', v)} prefix="$" /></Field>
          <Field label="Loan Term (years)"><Inp value={f.loan_term_years} onChange={(v: string) => s('loan_term_years', v)} /></Field>
          <CalcBtn onClick={calc} loading={loading} label="Calculate Buydown" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<div className="bg-gray-50 p-6 rounded-lg border">
          <div className="text-center mb-4 p-4 bg-white rounded-lg border"><p className="text-xs text-gray-500 uppercase">Total Savings</p><p className="text-3xl font-bold text-emerald-600">{fmt(result.total_savings)}</p></div>
          {result.break_even_months && <p className="text-sm text-center mb-3 text-gray-600">Break-even: {result.break_even_months} months</p>}
          <table className="w-full text-sm"><thead><tr className="border-b"><th className="text-left py-1">Year</th><th className="text-right">Rate</th><th className="text-right">Payment</th><th className="text-right">Savings/mo</th></tr></thead><tbody>
            {result.schedule?.map((y: any) => (<tr key={y.year} className="border-b"><td className="py-1">{y.year}</td><td className="text-right">{pct(y.rate)}</td><td className="text-right">{fmt(y.payment)}</td><td className="text-right text-emerald-600">{fmt(y.monthly_savings)}</td></tr>))}
          </tbody></table>
        </div>) : <Placeholder />}
        {result && <ShareOnlyBar result={result} inputData={f} sheetType="buydown" />}
        </div>
      </div>
    </div>
  );
}

// ── 7. EXTRA PAYMENT ──
function ExtraPaymentForm({ onBack }: { onBack: () => void }) {
  const [f, sF] = useState({ loan_amount: '280000', interest_rate: '7.0', loan_term_years: '30', extra_monthly: '200', extra_annual: '0', extra_one_time: '0' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/extra-payment', { loan_amount: parseFloat(f.loan_amount), interest_rate: parseFloat(f.interest_rate), loan_term_years: parseInt(f.loan_term_years), extra_monthly: parseFloat(f.extra_monthly), extra_annual: parseFloat(f.extra_annual), extra_one_time: parseFloat(f.extra_one_time) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="💰" name="Extra Payment" desc="See how extra payments accelerate payoff" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Section title="Loan Details" />
          <Field label="Loan Amount"><Inp value={f.loan_amount} onChange={(v: string) => s('loan_amount', v)} prefix="$" /></Field>
          <Field label="Interest Rate"><Inp value={f.interest_rate} onChange={(v: string) => s('interest_rate', v)} suffix="%" /></Field>
          <Field label="Loan Term (years)"><Inp value={f.loan_term_years} onChange={(v: string) => s('loan_term_years', v)} /></Field>
          <Section title="Extra Payments" />
          <Field label="Extra Monthly"><Inp value={f.extra_monthly} onChange={(v: string) => s('extra_monthly', v)} prefix="$" /></Field>
          <Field label="Extra Annual (yearly lump sum)"><Inp value={f.extra_annual} onChange={(v: string) => s('extra_annual', v)} prefix="$" /></Field>
          <Field label="One-Time Extra Payment"><Inp value={f.extra_one_time} onChange={(v: string) => s('extra_one_time', v)} prefix="$" /></Field>
          <CalcBtn onClick={calc} loading={loading} label="Calculate Savings" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<div className="bg-gray-50 p-6 rounded-lg border">
          <div className="text-center mb-4 p-4 bg-white rounded-lg border"><p className="text-xs text-gray-500 uppercase">Interest Saved</p><p className="text-3xl font-bold text-emerald-600">{fmt(result.savings?.interest_saved)}</p></div>
          <div className="text-center mb-4 p-4 bg-white rounded-lg border"><p className="text-xs text-gray-500 uppercase">Time Saved</p><p className="text-3xl font-bold text-blue-600">{result.savings?.years_saved ? parseFloat(result.savings.years_saved).toFixed(1) + ' years' : result.savings?.months_saved + ' months'}</p></div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="p-3 bg-white rounded border"><p className="text-xs text-gray-500">Standard</p><p className="font-semibold">{result.standard?.months ? Math.round(result.standard.months / 12) + ' yrs' : '-'}</p><p className="text-xs text-gray-400">Interest: {fmt(result.standard?.total_interest)}</p></div>
            <div className="p-3 bg-white rounded border"><p className="text-xs text-gray-500">Accelerated</p><p className="font-semibold text-emerald-600">{result.accelerated?.months ? Math.round(result.accelerated.months / 12) + ' yrs' : '-'}</p><p className="text-xs text-gray-400">Interest: {fmt(result.accelerated?.total_interest)}</p></div>
          </div>
        </div>) : <Placeholder />}
        {result && <ShareOnlyBar result={result} inputData={f} sheetType="extra-payment" />}
        </div>
      </div>
    </div>
  );
}

// ── 8. BUY NOW VS LATER ──
function BuyNowForm({ onBack }: { onBack: () => void }) {
  const [f, sF] = useState({ current_price: '350000', current_rate: '7.0', loan_amount_pct: '80', annual_appreciation_pct: '3.0', rate_change_per_year: '0.25', monthly_rent_if_waiting: '1800', loan_term_years: '30' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/buy-now-vs-later', { current_price: parseFloat(f.current_price), current_rate: parseFloat(f.current_rate), loan_amount_pct: parseFloat(f.loan_amount_pct), annual_appreciation_pct: parseFloat(f.annual_appreciation_pct), rate_change_per_year: parseFloat(f.rate_change_per_year), monthly_rent_if_waiting: parseFloat(f.monthly_rent_if_waiting), loan_term_years: parseInt(f.loan_term_years) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="⏳" name="Buy Now vs Later" desc="Show clients the cost of waiting to buy" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Field label="Current Home Price"><Inp value={f.current_price} onChange={(v: string) => s('current_price', v)} prefix="$" /></Field>
          <Field label="Current Interest Rate"><Inp value={f.current_rate} onChange={(v: string) => s('current_rate', v)} suffix="%" /></Field>
          <Field label="Down Payment % (LTV)"><Inp value={f.loan_amount_pct} onChange={(v: string) => s('loan_amount_pct', v)} suffix="%" /></Field>
          <Field label="Annual Appreciation"><Inp value={f.annual_appreciation_pct} onChange={(v: string) => s('annual_appreciation_pct', v)} suffix="%" /></Field>
          <Field label="Rate Change Per Year"><Inp value={f.rate_change_per_year} onChange={(v: string) => s('rate_change_per_year', v)} suffix="%" /></Field>
          <Field label="Monthly Rent While Waiting"><Inp value={f.monthly_rent_if_waiting} onChange={(v: string) => s('monthly_rent_if_waiting', v)} prefix="$" /></Field>
          <CalcBtn onClick={calc} loading={loading} label="Compare Buy Now vs Wait" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<div className="bg-gray-50 p-6 rounded-lg border">
          {result.current_scenario && (<div className="mb-4 p-4 bg-emerald-50 border border-emerald-200 rounded"><p className="text-xs text-emerald-700 uppercase font-semibold">Buy Now</p><p className="text-lg font-bold">{fmt(result.current_scenario.price)} at {pct(result.current_scenario.rate)}</p><p className="text-sm text-gray-600">Monthly: {fmt(result.current_scenario.monthly_payment)}</p></div>)}
          {result.future_scenarios?.map((sc: any, i: number) => (<div key={i} className="mb-3 p-4 bg-red-50 border border-red-200 rounded"><p className="text-xs text-red-700 uppercase font-semibold">Wait {sc.months_waited} months</p><p className="text-lg font-bold">{fmt(sc.price)} at {pct(sc.rate)}</p><p className="text-sm text-gray-600">Monthly: {fmt(sc.monthly_payment)} (+{fmt(sc.payment_increase)}/mo)</p><p className="text-sm text-red-600 font-semibold">Cost of waiting: {fmt(sc.total_cost_of_waiting)}</p></div>))}
          {result.recommendation && <p className="text-sm mt-3 p-3 bg-blue-50 border border-blue-200 rounded">{result.recommendation}</p>}
        </div>) : <Placeholder />}
        {result && <ShareOnlyBar result={result} inputData={f} sheetType="buy-now-vs-later" />}
        </div>
      </div>
    </div>
  );
}

// ── 9. PRICE VS RATE ──
function PriceVsRateForm({ onBack }: { onBack: () => void }) {
  const [f, sF] = useState({ base_price: '350000', base_rate: '7.0', loan_amount_pct: '80', loan_term_years: '30' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/price-vs-rate', { base_price: parseFloat(f.base_price), base_rate: parseFloat(f.base_rate), loan_amount_pct: parseFloat(f.loan_amount_pct), loan_term_years: parseInt(f.loan_term_years) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="📈" name="Price vs Rate Matrix" desc="See how price and rate changes impact payments" onBack={onBack} />
      <div className="space-y-3 max-w-md">
        <Field label="Base Home Price"><Inp value={f.base_price} onChange={(v: string) => s('base_price', v)} prefix="$" /></Field>
        <Field label="Base Interest Rate"><Inp value={f.base_rate} onChange={(v: string) => s('base_rate', v)} suffix="%" /></Field>
        <Field label="Loan-to-Value"><Inp value={f.loan_amount_pct} onChange={(v: string) => s('loan_amount_pct', v)} suffix="%" /></Field>
        <Field label="Loan Term (years)"><Inp value={f.loan_term_years} onChange={(v: string) => s('loan_term_years', v)} /></Field>
        <CalcBtn onClick={calc} loading={loading} label="Generate Matrix" /><ErrMsg error={error} />
      </div>
      {result?.matrix && (<div className="mt-6 overflow-x-auto"><p className="text-sm text-gray-600 mb-2">Base payment: {fmt(result.base_payment)}</p>
        <table className="w-full text-sm border"><thead><tr className="bg-gray-100"><th className="p-2 border text-left">Price</th><th className="p-2 border">Rate</th><th className="p-2 border">Payment</th><th className="p-2 border">Delta</th></tr></thead><tbody>
          {result.matrix.map((cell: any, i: number) => (<tr key={i} className="border-b"><td className="p-2 border">{fmt(cell.price)}</td><td className="p-2 border text-center">{pct(cell.rate)}</td><td className="p-2 border text-center font-medium">{fmt(cell.monthly_payment)}</td><td className={`p-2 border text-center ${parseFloat(cell.payment_delta) > 0 ? 'text-red-600' : 'text-emerald-600'}`}>{parseFloat(cell.payment_delta) > 0 ? '+' : ''}{fmt(cell.payment_delta)}</td></tr>))}
        </tbody></table>
      </div>)}
      {result && <ShareOnlyBar result={result} inputData={f} sheetType="price-vs-rate" />}
    </div>
  );
}

// ── 10. SCENARIO COMPARE ──
function ScenarioCompareForm({ counties, onBack }: { counties: any[]; onBack: () => void }) {
  const [f, sF] = useState({ county_id: counties[0]?.id?.toString() || '1', existing_loan_balance: '150000', seller_agent_commission_pct: '3.0', include_home_warranty: true, a_offer_price: '340000', a_buyer_agent_pct: '3.0', a_seller_concessions: '5000', a_notes: '', b_offer_price: '350000', b_buyer_agent_pct: '2.5', b_seller_concessions: '0', b_notes: '' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/scenario-compare', { county_id: parseInt(f.county_id), existing_loan_balance: parseFloat(f.existing_loan_balance), seller_agent_commission_pct: parseFloat(f.seller_agent_commission_pct), include_home_warranty: f.include_home_warranty, scenario_a: { offer_price: parseFloat(f.a_offer_price), buyer_agent_pct: parseFloat(f.a_buyer_agent_pct), seller_concessions: parseFloat(f.a_seller_concessions), notes: f.a_notes }, scenario_b: { offer_price: parseFloat(f.b_offer_price), buyer_agent_pct: parseFloat(f.b_buyer_agent_pct), seller_concessions: parseFloat(f.b_seller_concessions), notes: f.b_notes } }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="🔄" name="Scenario Compare" desc="Compare two offers side-by-side" onBack={onBack} />
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Field label="County"><select value={f.county_id} onChange={e => s('county_id', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">{counties.map((c: any) => <option key={c.id} value={c.id}>{c.county_name}, {c.state}</option>)}</select></Field>
          <Field label="Existing Loan Balance"><Inp value={f.existing_loan_balance} onChange={(v: string) => s('existing_loan_balance', v)} prefix="$" /></Field>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Seller Agent Commission"><Inp value={f.seller_agent_commission_pct} onChange={(v: string) => s('seller_agent_commission_pct', v)} suffix="%" /></Field>
          <div className="flex items-end pb-2"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.include_home_warranty} onChange={e => s('include_home_warranty', e.target.checked)} /> Home Warranty</label></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
            <h4 className="font-semibold text-blue-800">Offer A</h4>
            <Field label="Offer Price"><Inp value={f.a_offer_price} onChange={(v: string) => s('a_offer_price', v)} prefix="$" /></Field>
            <Field label="Buyer Agent Commission"><Inp value={f.a_buyer_agent_pct} onChange={(v: string) => s('a_buyer_agent_pct', v)} suffix="%" /></Field>
            <Field label="Seller Concessions"><Inp value={f.a_seller_concessions} onChange={(v: string) => s('a_seller_concessions', v)} prefix="$" /></Field>
            <Field label="Notes"><Inp type="text" value={f.a_notes} onChange={(v: string) => s('a_notes', v)} placeholder="Cash buyer, quick close" /></Field>
          </div>
          <div className="p-4 bg-pink-50 border border-pink-200 rounded-lg space-y-3">
            <h4 className="font-semibold text-pink-800">Offer B</h4>
            <Field label="Offer Price"><Inp value={f.b_offer_price} onChange={(v: string) => s('b_offer_price', v)} prefix="$" /></Field>
            <Field label="Buyer Agent Commission"><Inp value={f.b_buyer_agent_pct} onChange={(v: string) => s('b_buyer_agent_pct', v)} suffix="%" /></Field>
            <Field label="Seller Concessions"><Inp value={f.b_seller_concessions} onChange={(v: string) => s('b_seller_concessions', v)} prefix="$" /></Field>
            <Field label="Notes"><Inp type="text" value={f.b_notes} onChange={(v: string) => s('b_notes', v)} placeholder="FHA, 45-day close" /></Field>
          </div>
        </div>
        <CalcBtn onClick={calc} loading={loading} label="Compare Offers" /><ErrMsg error={error} />
      </div>
      {result && (<div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={`p-5 rounded-lg border-2 ${parseFloat(result.difference) >= 0 ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-gray-50'}`}>
          <p className="text-xs uppercase font-semibold text-blue-700">Offer A Net</p><p className="text-3xl font-bold mt-1">{fmt(result.scenario_a?.net_proceeds)}</p>
          {result.scenario_a?.line_items?.map((item: any, i: number) => (<div key={i} className="flex justify-between text-sm py-0.5"><span>{item.label}</span><span>{fmt(item.amount)}</span></div>))}
        </div>
        <div className={`p-5 rounded-lg border-2 ${parseFloat(result.difference) < 0 ? 'border-pink-400 bg-pink-50' : 'border-gray-200 bg-gray-50'}`}>
          <p className="text-xs uppercase font-semibold text-pink-700">Offer B Net</p><p className="text-3xl font-bold mt-1">{fmt(result.scenario_b?.net_proceeds)}</p>
          {result.scenario_b?.line_items?.map((item: any, i: number) => (<div key={i} className="flex justify-between text-sm py-0.5"><span>{item.label}</span><span>{fmt(item.amount)}</span></div>))}
        </div>
        <div className="md:col-span-2 text-center p-4 bg-white rounded-lg border-2 border-gray-300">
          <p className="text-sm text-gray-500">Difference</p><p className="text-2xl font-bold">{fmt(Math.abs(parseFloat(result.difference)))}</p>
          <p className="text-sm text-gray-600 mt-1">{result.recommendation}</p>
        </div>
      </div>)}
      {result && <ShareOnlyBar result={result} inputData={f} sheetType="scenario-compare" />}
    </div>
  );
}

// ── 11. BUYER COMPENSATION (Post-NAR) ──
function BuyerCompensationForm({ onBack }: { onBack: () => void }) {
  const [f, sF] = useState({ purchase_price: '350000', loan_amount: '280000', seller_offered_compensation_pct: '3.0', buyer_agent_fee_pct: '2.5', compensation_structure: 'split', flat_fee_amount: '0', interest_rate: '7.0', loan_term_years: '30' });
  const [result, setResult] = useState<any>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const s = (k: string, v: any) => sF(p => ({ ...p, [k]: v }));
  const calc = async () => { setLoading(true); setError(''); try { const res = await api.post('/calculators/buyer-compensation', { purchase_price: parseFloat(f.purchase_price), loan_amount: parseFloat(f.loan_amount), seller_offered_compensation_pct: parseFloat(f.seller_offered_compensation_pct), buyer_agent_fee_pct: parseFloat(f.buyer_agent_fee_pct), compensation_structure: f.compensation_structure, flat_fee_amount: parseFloat(f.flat_fee_amount), interest_rate: parseFloat(f.interest_rate), loan_term_years: parseInt(f.loan_term_years) }); setResult(res.data); } catch (e: any) { setError(e.response?.data?.detail || 'Calculation failed'); } setLoading(false); };
  return (
    <div className="mt-4"><Header icon="🤝" name="Buyer Compensation" desc="Post-NAR settlement compensation analysis" onBack={onBack} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <Section title="Transaction" />
          <Field label="Purchase Price"><Inp value={f.purchase_price} onChange={(v: string) => s('purchase_price', v)} prefix="$" /></Field>
          <Field label="Loan Amount"><Inp value={f.loan_amount} onChange={(v: string) => s('loan_amount', v)} prefix="$" /></Field>
          <Field label="Interest Rate"><Inp value={f.interest_rate} onChange={(v: string) => s('interest_rate', v)} suffix="%" /></Field>
          <Section title="Compensation" />
          <Field label="Seller Offered Compensation"><Inp value={f.seller_offered_compensation_pct} onChange={(v: string) => s('seller_offered_compensation_pct', v)} suffix="%" /></Field>
          <Field label="Buyer Agent Fee"><Inp value={f.buyer_agent_fee_pct} onChange={(v: string) => s('buyer_agent_fee_pct', v)} suffix="%" /></Field>
          <Field label="Structure"><select value={f.compensation_structure} onChange={e => s('compensation_structure', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"><option value="split">Split (seller + buyer)</option><option value="seller_pays">Seller Pays All</option><option value="buyer_pays">Buyer Pays All</option><option value="flat_fee">Flat Fee</option></select></Field>
          {f.compensation_structure === 'flat_fee' && <Field label="Flat Fee Amount"><Inp value={f.flat_fee_amount} onChange={(v: string) => s('flat_fee_amount', v)} prefix="$" /></Field>}
          <CalcBtn onClick={calc} loading={loading} label="Analyze Compensation" /><ErrMsg error={error} />
        </div>
        <div>{result ? (<div className="bg-gray-50 p-6 rounded-lg border">
          <div className="text-center mb-4 p-4 bg-white rounded-lg border"><p className="text-xs text-gray-500 uppercase">Total Agent Fee</p><p className="text-2xl font-bold">{fmt(result.total_agent_fee)}</p></div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="p-3 bg-white rounded border text-center"><p className="text-xs text-gray-500">Seller Pays</p><p className="text-lg font-bold text-emerald-600">{fmt(result.seller_contribution)}</p></div>
            <div className="p-3 bg-white rounded border text-center"><p className="text-xs text-gray-500">Buyer Out-of-Pocket</p><p className="text-lg font-bold text-red-600">{fmt(result.buyer_out_of_pocket)}</p></div>
          </div>
          {result.can_finance && <p className="text-sm p-2 bg-blue-50 border border-blue-200 rounded mb-3">Buyer portion can be financed into the loan</p>}
          {result.monthly_payment_impact && parseFloat(result.monthly_payment_impact) > 0 && <p className="text-sm text-gray-600">Monthly payment impact: +{fmt(result.monthly_payment_impact)}/mo</p>}
          {result.scenarios?.map((sc: any, i: number) => (<div key={i} className="mt-2 p-3 bg-white rounded border"><p className="font-medium text-sm">{sc.structure}</p><p className="text-xs text-gray-500">Buyer: {fmt(sc.buyer_cost)} | Seller: {fmt(sc.seller_cost)}</p>{sc.note && <p className="text-xs text-gray-400 mt-1">{sc.note}</p>}</div>))}
          {result.explainer_text && <p className="text-sm text-gray-600 mt-4 p-3 bg-gray-100 rounded">{result.explainer_text}</p>}
        </div>) : <Placeholder />}
        {result && <ShareOnlyBar result={result} inputData={f} sheetType="buyer-compensation" />}
        </div>
      </div>
    </div>
  );
}

// ── MAIN PAGE ──
export default function CalculatorPage() {
  const location = useLocation();
  const prefillState = location.state as { prefill?: any; sheetType?: string; openCalc?: string } | null;
  const [active, setActive] = useState<string | null>(
    prefillState?.openCalc ||
    (prefillState?.sheetType === 'seller' ? 'seller-net-sheet' :
    prefillState?.sheetType === 'buyer' ? 'buyer-estimate' : null)
  );
  const [prefill] = useState(prefillState?.prefill || null);
  const { data: counties } = useQuery({ queryKey: ['counties'], queryFn: () => api.get('/counties/').then(r => r.data) });
  const c = counties || [];
  const onBack = () => { setActive(null); window.history.replaceState({}, ''); };

  if (active === 'seller-net-sheet') return <div className="p-6 max-w-6xl mx-auto"><SellerForm counties={c} onBack={onBack} prefill={active === 'seller-net-sheet' ? prefill : undefined} /></div>;
  if (active === 'buyer-estimate') return <div className="p-6 max-w-6xl mx-auto"><BuyerForm counties={c} onBack={onBack} prefill={active === 'buyer-estimate' ? prefill : undefined} /></div>;
  if (active === 'truvalue') return <div className="p-6 max-w-6xl mx-auto"><TruValueForm counties={c} onBack={onBack} /></div>;
  if (active === 'scenario-compare') return <div className="p-6 max-w-6xl mx-auto"><ScenarioCompareForm counties={c} onBack={onBack} /></div>;
  if (active === 'buyer-compensation') return <div className="p-6 max-w-6xl mx-auto"><BuyerCompensationForm onBack={onBack} /></div>;
  if (active === 'buy-now-vs-later') return <div className="p-6 max-w-6xl mx-auto"><BuyNowForm onBack={onBack} /></div>;
  if (active === 'price-vs-rate') return <div className="p-6 max-w-6xl mx-auto"><PriceVsRateForm onBack={onBack} /></div>;
  if (active === 'extra-payment') return <div className="p-6 max-w-6xl mx-auto"><ExtraPaymentForm onBack={onBack} /></div>;
  if (active === 'sell-vs-rent') return <div className="p-6 max-w-6xl mx-auto"><SellVsRentForm onBack={onBack} /></div>;
  if (active === 'holding-cost') return <div className="p-6 max-w-6xl mx-auto"><HoldingCostForm onBack={onBack} /></div>;
  if (active === 'buydown') return <div className="p-6 max-w-6xl mx-auto"><BuydownForm onBack={onBack} /></div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Calculators</h1>
      <p className="text-gray-500 mb-6">11 calculators — select one to get started</p>
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Core Calculators</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {CALCS.slice(0, 2).map(c => (<button key={c.slug} onClick={() => setActive(c.slug)} className={`${c.color} border rounded-lg p-5 text-left transition-shadow cursor-pointer shadow-sm hover:shadow-md`}><div className="text-3xl mb-2">{c.icon}</div><h3 className="font-semibold text-gray-900">{c.name}</h3><p className="text-sm text-gray-600 mt-1">{c.desc}</p></button>))}
        </div>
      </div>
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Analysis Tools</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {CALCS.slice(2).map(c => (<button key={c.slug} onClick={() => setActive(c.slug)} className={`${c.color} border rounded-lg p-4 text-left transition-shadow cursor-pointer shadow-sm hover:shadow-md`}><div className="text-2xl mb-1">{c.icon}</div><h3 className="font-semibold text-gray-900 text-sm">{c.name}</h3><p className="text-xs text-gray-600 mt-1">{c.desc}</p></button>))}
        </div>
      </div>
    </div>
  );
}
