// JARVIS App — Shared TypeScript types  v2.0.0
// All API response shapes and domain models live here.
// AI-generated pages import from this file — never redefine types inline.
//
// v2.0.0: DEBT #22 fix — User has is_active boolean (matches backend
//         models/base.py User.is_active column).

// ── Auth ─────────────────────────────────────────────────────────────────────

export type UserRole = 'admin' | 'agent' | 'user';
export type UserStatus = 'active' | 'pending_approval' | 'inactive';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginInput {
  username: string; // FastAPI OAuth2 uses 'username' not 'email'
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
  [key: string]: unknown; // domain-specific fields added by AI
}

// ── Company / Branding ────────────────────────────────────────────────────────

export interface Company {
  id?: number;
  company_name: string;
  logo_url?: string | null;
  primary_color: string;
  secondary_color?: string;
  phone?: string;
  email?: string;
  website?: string;
  address?: string;
  tagline?: string;
  disclaimer_text?: string;
}

// ── Pagination ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ── API Error ─────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | { msg: string; type: string }[];
  status_code?: number;
}

// ── Utility ───────────────────────────────────────────────────────────────────

export function getErrorMessage(err: unknown): string {
  if (!err) return 'An unknown error occurred';
  const e = err as { response?: { data?: ApiError }; message?: string };
  const detail = e.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ');
  return e.message ?? 'An unknown error occurred';
}
