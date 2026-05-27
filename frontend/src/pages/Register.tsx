// TitleFlow — Registration Page v1.1.0
// v1.1.0: Added phone + brokerage_name fields for agent onboarding.
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
  phone: z.string().optional(),
  brokerage_name: z.string().optional(),
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
      void confirm_password;
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
          <div className="text-5xl mb-4">&#127881;</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">You are registered!</h2>
          <p className="text-gray-600 mb-2">
            Your account is pending approval by{' '}
            <strong>{company?.company_name || 'TitleFlow'}</strong>.
          </p>
          <p className="text-gray-500 text-sm">You will receive an email once your account is activated.</p>
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
            {company?.company_name || 'TitleFlow'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">Create your agent account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {/* Full Name */}
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
              <input id="full_name" type="text" autoComplete="name" {...register('full_name')}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] ${errors.full_name ? 'border-red-400' : 'border-gray-300'}`} />
              {errors.full_name && <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
              <input id="email" type="email" autoComplete="email" {...register('email')}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] ${errors.email ? 'border-red-400' : 'border-gray-300'}`} />
              {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
            </div>

            {/* Phone */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input id="phone" type="tel" autoComplete="tel" {...register('phone')}
                placeholder="(806) 555-1234"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]" />
            </div>

            {/* Brokerage */}
            <div>
              <label htmlFor="brokerage_name" className="block text-sm font-medium text-gray-700 mb-1">Brokerage / Company</label>
              <input id="brokerage_name" type="text" {...register('brokerage_name')}
                placeholder="ABC Realty Group"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)]" />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
              <input id="password" type="password" autoComplete="new-password" {...register('password')}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] ${errors.password ? 'border-red-400' : 'border-gray-300'}`} />
              {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-1">Confirm Password *</label>
              <input id="confirm_password" type="password" autoComplete="new-password" {...register('confirm_password')}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-brand)] ${errors.confirm_password ? 'border-red-400' : 'border-gray-300'}`} />
              {errors.confirm_password && <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>}
            </div>

            <button type="submit" disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-[var(--color-brand)] hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-lg transition-opacity">
              <UserPlus size={18} />
              {isSubmitting ? 'Creating account...' : 'Create account'}
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
