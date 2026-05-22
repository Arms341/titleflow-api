// JARVIS App — Navbar v2.0.0
// Shows company logo/name, nav links, and user info.
// Admin links visible only to admin role.
// v2.0.0: Added Calculators nav link to hub page.
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { LogOut, LayoutDashboard, FileText, ShoppingBag, Settings, Users, Calculator } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useBrand } from '@/contexts/BrandContext';

export default function Navbar() {
  const { user, logout, isAdmin } = useAuth();
  const { company } = useBrand();
  const navigate = useNavigate();

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-[var(--color-brand)] text-white'
        : 'text-gray-600 hover:bg-gray-100'
    }`;

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Logo / Brand */}
          <Link to="/dashboard" className="flex items-center gap-2 shrink-0">
            {company?.logo_url ? (
              <img src={company.logo_url} alt={company.company_name} className="h-8 w-auto" />
            ) : (
              <span className="text-lg font-bold text-[var(--color-brand)]">
                {company?.company_name || 'JARVIS App'}
              </span>
            )}
          </Link>

          {/* Agent nav links */}
          <div className="hidden md:flex items-center gap-1">
            <NavLink to="/dashboard" className={navLinkClass}>
              <LayoutDashboard size={16} /> Dashboard
            </NavLink>
            <NavLink to="/calculators" className={navLinkClass}>
              <Calculator size={16} /> Calculators
            </NavLink>
            <NavLink to="/saved-sheets" className={navLinkClass}>
              <FileText size={16} /> My Sheets
            </NavLink>
            <NavLink to="/orders" className={navLinkClass}>
              <ShoppingBag size={16} /> Orders
            </NavLink>
            {isAdmin && (
              <>
                <NavLink to="/admin/dashboard" className={navLinkClass}>
                  <Users size={16} /> Admin
                </NavLink>
                <NavLink to="/admin/settings" className={navLinkClass}>
                  <Settings size={16} /> Settings
                </NavLink>
              </>
            )}
          </div>

          {/* User info + logout */}
          <div className="flex items-center gap-3">
            {user && (
              <span className="hidden sm:block text-sm text-gray-600">
                {user.full_name || user.email}
              </span>
            )}
            <button
              onClick={() => { logout(); navigate('/login'); }}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-600 transition-colors"
              title="Logout"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
