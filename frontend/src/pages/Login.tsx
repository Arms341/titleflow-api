// HUB City Title — Login Page
// Branded login with navy/gold theme
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LogIn } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '@/contexts/AuthContext';
import { useBrand } from '@/contexts/BrandContext';
import { getErrorMessage } from '@/types';

const schema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});
type FormData = z.infer<typeof schema>;

export default function Login() {
  const { login } = useAuth();
  const { company } = useBrand();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  async function onSubmit(data: FormData) {
    try {
      await login(data.username, data.password);
      navigate(from, { replace: true });
    } catch (err) {
      const msg = getErrorMessage(err);
      if (msg.toLowerCase().includes('pending') || msg.toLowerCase().includes('approv')) {
        toast('Your account is pending approval.', { icon: '⏳', duration: 5000 });
      } else {
        toast.error(msg || 'Invalid credentials');
      }
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%)' }}>
      {/* Top bar */}
      <div className="w-full py-4 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {company?.logo_url && <div className="bg-white rounded-xl px-3 py-2 inline-block"><img src={company.logo_url} alt="" className="h-10" /></div>}
          <span className="text-white font-bold text-lg hidden sm:block">{company?.company_name || 'TitleFlow'}</span>
        </div>
        {company?.phone && <a href={`tel:${company.phone}`} className="text-blue-200 hover:text-white text-sm">{company.phone}</a>}
      </div>

      {/* Center card */}
      <div className="flex-1 flex items-center justify-center px-4 pb-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            {company?.logo_url ? (
              <div className="bg-white rounded-xl px-4 py-3 inline-block shadow-lg mb-4">
                <img src={company.logo_url} alt={company?.company_name} className="h-16 mx-auto" />
              </div>
            ) : (
              <h1 className="text-3xl font-bold text-white mb-2">{company?.company_name || 'TitleFlow'}</h1>
            )}
            {company?.tagline && <p className="text-blue-200 text-sm font-medium">{company.tagline}</p>}
          </div>

          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <h2 className="text-xl font-bold text-gray-900 mb-1">Welcome back</h2>
            <p className="text-gray-500 text-sm mb-6">Sign in to access your calculators and sheets</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input id="username" type="text" autoComplete="username" {...register('username')}
                  className={`w-full px-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-0 transition-colors ${errors.username ? 'border-red-400 focus:border-red-500' : 'border-gray-200 focus:border-blue-500'}`}
                  placeholder="agent@example.com" />
                {errors.username && <p className="mt-1 text-xs text-red-600">{errors.username.message}</p>}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input id="password" type="password" autoComplete="current-password" {...register('password')}
                  className={`w-full px-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-0 transition-colors ${errors.password ? 'border-red-400 focus:border-red-500' : 'border-gray-200 focus:border-blue-500'}`}
                  placeholder="••••••••" />
                {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
              </div>

              <button type="submit" disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 py-3.5 px-4 text-white font-bold rounded-xl transition-all hover:shadow-lg disabled:opacity-50"
                style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)' }}>
                <LogIn size={18} />
                {isSubmitting ? 'Signing in…' : 'Sign In'}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-gray-100 text-center">
              <p className="text-sm text-gray-500">
                Need an agent account?{' '}
                <Link to="/register" className="text-blue-600 hover:underline font-semibold">Register</Link>
              </p>
            </div>
          </div>

          {/* Footer info */}
          <div className="mt-8 text-center">
            {company?.address && <p className="text-blue-200 text-xs">{company.address}</p>}
            <p className="text-blue-300/50 text-xs mt-2">Powered by TitleFlow</p>
          </div>
        </div>
      </div>
    </div>
  );
}
