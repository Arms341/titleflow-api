// ProfilePage.tsx v1.0.0
// Agent profile editor — edit name, phone, brokerage, license, avatar URL.
// Calls PUT /auth/profile to persist changes.
import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { User as UserIcon, Building2, Phone, CreditCard, Camera, Save, CheckCircle } from 'lucide-react';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    brokerage_name: '',
    license_number: '',
    avatar_url: '',
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (user) {
      setForm({
        full_name: user.full_name || '',
        phone: user.phone || '',
        brokerage_name: (user as any).brokerage_name || '',
        license_number: (user as any).license_number || '',
        avatar_url: user.avatar_url || '',
      });
    }
  }, [user]);

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.put('/auth/profile', data).then(r => r.data),
    onSuccess: () => {
      setSaved(true);
      refreshUser();
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(form);
  };

  const update = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">My Profile</h1>
      <p className="text-gray-500 mb-6">Update your agent information. This appears on PDFs and shared sheets.</p>

      <div className="bg-white rounded-lg shadow border p-6">
        {/* Avatar preview */}
        <div className="flex items-center gap-4 mb-8 pb-6 border-b">
          <div className="w-20 h-20 rounded-full bg-gray-100 border-2 border-gray-200 flex items-center justify-center overflow-hidden shrink-0">
            {form.avatar_url ? (
              <img src={form.avatar_url} alt="Profile" className="w-full h-full object-cover"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
            ) : (
              <UserIcon size={32} className="text-gray-400" />
            )}
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-lg">{form.full_name || user?.email || 'Agent'}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
            {form.brokerage_name && <p className="text-sm text-gray-400">{form.brokerage_name}</p>}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Full Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <UserIcon size={14} className="inline mr-1.5 mb-0.5" />Full Name
            </label>
            <input type="text" value={form.full_name} onChange={e => update('full_name', e.target.value)}
              placeholder="John Smith"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Phone size={14} className="inline mr-1.5 mb-0.5" />Phone
            </label>
            <input type="tel" value={form.phone} onChange={e => update('phone', e.target.value)}
              placeholder="(806) 555-1234"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" />
          </div>

          {/* Brokerage Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Building2 size={14} className="inline mr-1.5 mb-0.5" />Brokerage / Company
            </label>
            <input type="text" value={form.brokerage_name} onChange={e => update('brokerage_name', e.target.value)}
              placeholder="ABC Realty Group"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" />
          </div>

          {/* License Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <CreditCard size={14} className="inline mr-1.5 mb-0.5" />License Number
            </label>
            <input type="text" value={form.license_number} onChange={e => update('license_number', e.target.value)}
              placeholder="TX-123456"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" />
          </div>

          {/* Avatar Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Camera size={14} className="inline mr-1.5 mb-0.5" />Headshot Photo
            </label>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gray-100 border-2 border-gray-200 flex items-center justify-center overflow-hidden shrink-0">
                {form.avatar_url ? (
                  <img src={form.avatar_url} alt="Preview" className="w-full h-full object-cover"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                ) : (
                  <UserIcon size={24} className="text-gray-400" />
                )}
              </div>
              <div className="flex-1">
                <input type="file" accept="image/*" className="hidden" id="avatar-upload"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    if (file.size > 5 * 1024 * 1024) { alert('Photo must be under 5MB'); return; }
                    // Resize to 300x300 max for PDF headshot
                    const img = document.createElement('img');
                    const canvas = document.createElement('canvas');
                    const reader = new FileReader();
                    reader.onload = () => {
                      img.onload = () => {
                        const max = 300;
                        let w = img.width, h = img.height;
                        if (w > h) { if (w > max) { h = h * max / w; w = max; } }
                        else { if (h > max) { w = w * max / h; h = max; } }
                        canvas.width = w; canvas.height = h;
                        canvas.getContext('2d')!.drawImage(img, 0, 0, w, h);
                        const resized = canvas.toDataURL('image/jpeg', 0.85);
                        update('avatar_url', resized);
                      };
                      img.src = reader.result as string;
                    };
                    reader.readAsDataURL(file);
                  }} />
                <label htmlFor="avatar-upload"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer text-sm font-medium">
                  <Camera size={16} />
                  {form.avatar_url ? 'Change Photo' : 'Upload Photo'}
                </label>
                <p className="text-xs text-gray-400 mt-1">JPG or PNG, max 2MB. Appears on PDFs sent to clients.</p>
              </div>
            </div>
          </div>

          {/* Submit */}
          <div className="pt-4 border-t flex items-center justify-between">
            <div>
              {saved && (
                <span className="text-emerald-600 text-sm font-medium flex items-center gap-1">
                  <CheckCircle size={16} /> Profile saved!
                </span>
              )}
              {mutation.isError && (
                <span className="text-red-600 text-sm">
                  Save failed: {(mutation.error as any)?.response?.data?.detail || 'Unknown error'}
                </span>
              )}
            </div>
            <button type="submit" disabled={mutation.isPending}
              className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm disabled:opacity-50">
              <Save size={16} />
              {mutation.isPending ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
