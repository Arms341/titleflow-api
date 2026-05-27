// SharedSheetPage.tsx v1.0.0
// Public page — NO auth required. Client views branded net sheet + signs.
// Canvas signature pad with touch support (works on phone).
import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8765';
const fmt = (v: any) => { if (v == null) return '-'; const n = typeof v === 'string' ? parseFloat(v) : v; if (isNaN(n)) return '-'; return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n); };

function SignaturePad({ onSign }: { onSign: (dataUrl: string) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [drawing, setDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);

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
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const getPos = (e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    if ('touches' in e) {
      return { x: e.touches[0].clientX - rect.left, y: e.touches[0].clientY - rect.top };
    }
    return { x: (e as React.MouseEvent).clientX - rect.left, y: (e as React.MouseEvent).clientY - rect.top };
  };

  const start = (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const pos = getPos(e);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
    setDrawing(true);
    setHasDrawn(true);
  };

  const draw = (e: React.MouseEvent | React.TouchEvent) => {
    if (!drawing) return;
    e.preventDefault();
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const pos = getPos(e);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  };

  const stop = () => setDrawing(false);

  const clear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawn(false);
  };

  const submit = () => {
    if (!canvasRef.current || !hasDrawn) return;
    onSign(canvasRef.current.toDataURL('image/png'));
  };

  return (
    <div>
      <p className="text-sm text-gray-600 mb-2">Draw your signature below:</p>
      <div className="border-2 border-gray-300 rounded-lg bg-white relative" style={{ touchAction: 'none' }}>
        <canvas ref={canvasRef} className="w-full cursor-crosshair" style={{ height: '150px' }}
          onMouseDown={start} onMouseMove={draw} onMouseUp={stop} onMouseLeave={stop}
          onTouchStart={start} onTouchMove={draw} onTouchEnd={stop} />
        <div className="absolute bottom-2 left-3 right-3 border-b border-gray-300" />
        <span className="absolute bottom-1 left-3 text-xs text-gray-400">Sign here</span>
      </div>
      <div className="flex gap-2 mt-2">
        <button onClick={clear} className="px-4 py-2 text-sm text-gray-600 border rounded-lg hover:bg-gray-50">Clear</button>
        <button onClick={submit} disabled={!hasDrawn}
          className="flex-1 px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-semibold disabled:opacity-40 disabled:cursor-not-allowed">
          Confirm Signature
        </button>
      </div>
    </div>
  );
}

export default function SharedSheetPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [signed, setSigned] = useState(false);
  const [signing, setSigning] = useState(false);
  const [signerName, setSignerName] = useState('');

  const token = window.location.pathname.split('/shared/')[1];

  useEffect(() => {
    if (!token) { setError('Invalid share link'); setLoading(false); return; }
    axios.get(`${API}/shared/${token}`)
      .then(res => { setData(res.data); if (res.data.sheet?.is_signed) setSigned(true); })
      .catch(e => setError(e.response?.data?.detail || 'Sheet not found'))
      .finally(() => setLoading(false));
  }, [token]);

  const handleSign = async (signatureDataUrl: string) => {
    setSigning(true);
    try {
      await axios.post(`${API}/shared/${token}/sign`, { signature: signatureDataUrl, signer_name: signerName });
      setSigned(true);
    } catch (e: any) { alert(e.response?.data?.detail || 'Signature failed'); }
    setSigning(false);
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" /></div>;
  if (error) return <div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="text-center"><p className="text-6xl mb-4">&#128683;</p><p className="text-gray-700 text-lg">{error}</p></div></div>;
  if (!data) return null;

  const { sheet, branding } = data;
  const out = sheet.output_data || {};
  const inp = sheet.input_data || {};

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Branded Header */}
      <div className="shadow-md" style={{ background: `linear-gradient(135deg, ${branding.primary_color || '#0f172a'} 0%, #1e3a8a 100%)` }}>
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {branding.logo_url && (
              <div className="bg-white rounded-lg px-2 py-1">
                <img src={branding.logo_url} alt={branding.company_name} className="h-8 w-auto" />
              </div>
            )}
            <span className="text-white font-bold text-lg">{branding.company_name}</span>
          </div>
          {branding.phone && <a href={`tel:${branding.phone}`} className="text-blue-200 text-sm hover:text-white">{branding.phone}</a>}
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Sheet Type Badge */}
        <div className="text-center mb-6">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${sheet.sheet_type === 'seller' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}`}>
            {sheet.sheet_type === 'seller' ? 'Seller Net Sheet' : 'Buyer Estimate'}
          </span>
          <h1 className="text-2xl font-bold text-gray-900 mt-3">{sheet.property_address || 'Property Estimate'}</h1>
          <p className="text-gray-500 text-sm mt-1">
            Prepared for {sheet.client_name || 'Client'} &bull; {sheet.created_at ? new Date(sheet.created_at).toLocaleDateString() : ''}
          </p>
        </div>

        {/* Main Result */}
        <div className="bg-white rounded-xl shadow-lg border p-6 mb-6">
          {out.net_proceeds != null && (
            <div className="text-center mb-6 p-5 bg-emerald-50 rounded-lg border border-emerald-200">
              <p className="text-xs text-emerald-600 uppercase tracking-wide font-semibold">Estimated Net Proceeds</p>
              <p className="text-4xl font-bold text-emerald-700 mt-1">{fmt(out.net_proceeds)}</p>
            </div>
          )}
          {out.cash_to_close != null && (
            <div className="text-center mb-6 p-5 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs text-blue-600 uppercase tracking-wide font-semibold">Estimated Cash to Close</p>
              <p className="text-4xl font-bold text-blue-700 mt-1">{fmt(out.cash_to_close)}</p>
            </div>
          )}

          {/* Line Items */}
          {out.line_items?.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-700 text-sm uppercase mb-3">Closing Cost Breakdown</h3>
              <div className="space-y-0.5">
                {out.line_items.map((item: any, i: number) => (
                  <div key={i} className="flex justify-between text-sm py-2 border-b border-gray-100">
                    <span className="text-gray-700">{item.label}</span>
                    <span className="font-medium text-gray-900">{fmt(item.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            {out.sale_price != null && <div className="flex justify-between text-sm"><span>Sale Price</span><span className="font-semibold">{fmt(out.sale_price)}</span></div>}
            {out.purchase_price != null && <div className="flex justify-between text-sm"><span>Purchase Price</span><span className="font-semibold">{fmt(out.purchase_price)}</span></div>}
            {out.total_closing_costs != null && <div className="flex justify-between text-sm"><span>Total Closing Costs</span><span className="font-semibold text-red-600">-{fmt(out.total_closing_costs)}</span></div>}
            {out.loan_payoff != null && <div className="flex justify-between text-sm"><span>Loan Payoff</span><span className="font-semibold text-red-600">-{fmt(out.loan_payoff)}</span></div>}
          </div>
        </div>

        {/* Signature Section */}
        <div className="bg-white rounded-xl shadow-lg border p-6 mb-6">
          {signed ? (
            <div className="text-center py-4">
              <p className="text-3xl mb-2">&#9989;</p>
              <p className="font-bold text-emerald-800 text-lg">Signed</p>
              <p className="text-sm text-gray-500 mt-1">
                {sheet.signed_at ? `Signed on ${new Date(sheet.signed_at).toLocaleDateString()}` : 'Signature recorded'}
              </p>
            </div>
          ) : (
            <>
              <h3 className="font-semibold text-gray-900 mb-1">Client Acknowledgment</h3>
              <p className="text-sm text-gray-500 mb-4">
                By signing below, you acknowledge that you have reviewed this {sheet.sheet_type === 'seller' ? 'seller net sheet' : 'buyer estimate'} and that the figures shown are estimates only. Actual amounts may vary at closing.
              </p>
              <div className="mb-3">
                <label className="block text-xs text-gray-500 mb-1">Your Name</label>
                <input type="text" value={signerName} onChange={e => setSignerName(e.target.value)}
                  placeholder={sheet.client_name || 'Full Name'}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              {signing ? (
                <div className="text-center py-4"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto" /></div>
              ) : (
                <SignaturePad onSign={handleSign} />
              )}
            </>
          )}
        </div>

        {/* Disclaimer */}
        <div className="text-center text-xs text-gray-400 mb-8">
          {branding.disclaimer_text || 'This is an estimate only. Actual closing costs may vary. Contact your title company for final figures.'}
          <br />
          <span className="mt-2 inline-block">Powered by {branding.company_name} &bull; {branding.website && <a href={branding.website} className="underline">{branding.website.replace('https://', '')}</a>}</span>
        </div>
      </div>
    </div>
  );
}
