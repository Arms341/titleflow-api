// JARVIS App — Brand / Company Context  v2.0.1
// Loads GET /company on mount. Applies CSS variables for brand colors.
// Provides useBrand() hook — AI-generated pages use this for company name, logo, colors.
// v2.0.1: Fixed TS2345 — applyBrandColors accepts string | undefined.
// v2.0.0: normalizeColor() ensures # prefix — DB stores hex without #, CSS needs it.
import React, {
  createContext, useContext, useEffect, useState,
  type ReactNode,
} from 'react';
import api from '@/lib/api';
import type { Company } from '@/types';

// ── Context shape ─────────────────────────────────────────────────────────────

interface BrandContextValue {
  company: Company | null;
  isLoading: boolean;
  primaryColor: string;
  secondaryColor: string;
}

const DEFAULT_PRIMARY = '#1D4ED8';
const DEFAULT_SECONDARY = '#6B7280';

const BrandContext = createContext<BrandContextValue>({
  company: null,
  isLoading: true,
  primaryColor: DEFAULT_PRIMARY,
  secondaryColor: DEFAULT_SECONDARY,
});

// ── Normalize color: ensure # prefix ──────────────────────────────────────────

function normalizeColor(color: string | null | undefined, fallback: string): string {
  if (!color) return fallback;
  const trimmed = color.trim();
  if (!trimmed) return fallback;
  return trimmed.startsWith('#') ? trimmed : `#${trimmed}`;
}

// ── Apply CSS variables helper ────────────────────────────────────────────────

function applyBrandColors(primary: string | undefined, secondary: string | undefined) {
  const root = document.documentElement;
  const p = normalizeColor(primary, DEFAULT_PRIMARY);
  const s = normalizeColor(secondary, DEFAULT_SECONDARY);
  root.style.setProperty('--color-brand', p);
  root.style.setProperty('--color-brand-secondary', s);
  root.style.setProperty('--color-brand-hover', p + 'DD');
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function BrandProvider({ children }: { children: ReactNode }) {
  const [company, setCompany] = useState<Company | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get<Company>('/company')
      .then((res) => {
        setCompany(res.data);
        applyBrandColors(res.data.primary_color, res.data.secondary_color);
      })
      .catch(() => {
        applyBrandColors(DEFAULT_PRIMARY, DEFAULT_SECONDARY);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const primaryColor = normalizeColor(company?.primary_color, DEFAULT_PRIMARY);
  const secondaryColor = normalizeColor(company?.secondary_color, DEFAULT_SECONDARY);

  return (
    <BrandContext.Provider value={{ company, isLoading, primaryColor, secondaryColor }}>
      {children}
    </BrandContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useBrand(): BrandContextValue {
  return useContext(BrandContext);
}

export default BrandProvider;
