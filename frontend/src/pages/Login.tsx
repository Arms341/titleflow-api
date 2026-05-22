// JARVIS App — Login Page
// react-hook-form + Zod. Sends OAuth2 form-encoded credentials.
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
      // Pending approval — show friendly message not toast
      if (msg.toLowerCase().includes('pending') || msg.toLowerCase().includes('approv')) {
        toast('Your account is pending approval.', { icon: '⏳', duration: 5000 });
      } else {
        toast.error(msg || 'Invalid credentials');
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">

        {/* Brand header */}
        <div className="text-center mb-8">
          {company?.logo_url ? (
            <img src={company.logo_url} alt={company.company_name} className="h-12 mx-auto mb-3" />
          ) : (
            <h1 className="text-2xl font-bold text-[var(--color-brand)] mb-1">
              {company?.company_name || 'JARVIS App'}
            </h1>
          )}
          {company?.tagline && (
            <p className="text-sm text-gray-500">{company.tagline}</p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Username or Email
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                {...register('username')}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] ${
                  errors.username ? 'border-red-400' : 'border-gray-300'
                }`}
              />
              {errors.username && (
                <p className="mt-1 text-xs text-red-600">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register('password')}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] ${
                  errors.password ? 'border-red-400' : 'border-gray-300'
                }`}
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-[var(--color-brand)] hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-lg transition-opacity"
            >
              <LogIn size={18} />
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-600">
            Need access?{' '}
            <Link to="/register" className="text-[var(--color-brand)] hover:underline font-medium">
              Register for free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
