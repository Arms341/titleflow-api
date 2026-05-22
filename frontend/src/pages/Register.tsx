// JARVIS App — Registration Page
// react-hook-form + Zod. Submission does NOT auto-login (admin approval required).
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '@/contexts/AuthContext';
import { useBrand } from '@/contexts/BrandContext';
import { getErrorMessage } from '@/types';

const schema = z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
  full_name: z.string().min(2, 'Full name required'),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});
type FormData = z.infer<typeof schema>;

export default function Register() {
  const { register: registerUser } = useAuth();
  const { company } = useBrand();
  const [submitted, setSubmitted] = useState(false);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  async function onSubmit(data: FormData) {
    try {
      const { confirm_password, ...payload } = data;
      void confirm_password; // used only for validation
      await registerUser(payload);
      setSubmitted(true);
    } catch (err) {
      toast.error(getErrorMessage(err) || 'Registration failed');
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md text-center bg-white rounded-2xl shadow-lg p-10">
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">You're registered!</h2>
          <p className="text-gray-600 mb-2">
            Your account is pending approval by{' '}
            <strong>{company?.company_name || 'JARVIS App'}</strong>.
          </p>
          <p className="text-gray-500 text-sm">You'll receive an email once your account is activated.</p>
          <Link to="/login" className="mt-6 inline-block text-sm text-[var(--color-brand)] hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[var(--color-brand)]">
            {company?.company_name || 'JARVIS App'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">Create your free account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {[
              { name: 'full_name'        as const, label: 'Full Name',        type: 'text',     auto: 'name' },
              { name: 'email'            as const, label: 'Email Address',    type: 'email',    auto: 'email' },
              { name: 'password'         as const, label: 'Password',         type: 'password', auto: 'new-password' },
              { name: 'confirm_password' as const, label: 'Confirm Password', type: 'password', auto: 'new-password' },
            ].map(({ name, label, type, auto }) => (
              <div key={name}>
                <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
                  {label}
                </label>
                <input
                  id={name}
                  type={type}
                  autoComplete={auto}
                  {...register(name)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] ${
                    errors[name] ? 'border-red-400' : 'border-gray-300'
                  }`}
                />
                {errors[name] && (
                  <p className="mt-1 text-xs text-red-600">{errors[name]?.message}</p>
                )}
              </div>
            ))}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-[var(--color-brand)] hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-lg transition-opacity"
            >
              <UserPlus size={18} />
              {isSubmitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-[var(--color-brand)] hover:underline font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
