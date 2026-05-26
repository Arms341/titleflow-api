// HUB City Title — Navbar v3.0.0
// Navy branded header with logo, nav links, user info
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { LogOut, LayoutDashboard, FileText, ShoppingBag, Calculator } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useBrand } from '@/contexts/BrandContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { company } = useBrand();
  const navigate = useNavigate();

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-white/20 text-white'
        : 'text-blue-100 hover:bg-white/10 hover:text-white'
    }`;

  return (
    <nav className="sticky top-0 z-40 shadow-md" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">

          <Link to="/dashboard" className="flex items-center gap-2.5 shrink-0">
            {company?.logo_url ? (
              <div className="bg-white rounded-lg px-2 py-1">
                <img src={company.logo_url} alt={company.company_name} className="h-8 w-auto" />
              </div>
            ) : (
              <span className="text-white font-bold text-base">
                {company?.company_name || 'TitleFlow'}
              </span>
            )}
          </Link>

          <div className="hidden md:flex items-center gap-1">
            <NavLink to="/dashboard" className={navLinkClass}>
              <LayoutDashboard size={15} /> Dashboard
            </NavLink>
            <NavLink to="/calculators" className={navLinkClass}>
              <Calculator size={15} /> Calculators
            </NavLink>
            <NavLink to="/saved-sheets" className={navLinkClass}>
              <FileText size={15} /> My Sheets
            </NavLink>
            <NavLink to="/orders" className={navLinkClass}>
              <ShoppingBag size={15} /> Orders
            </NavLink>
          </div>

          <div className="flex items-center gap-3">
            {user && (
              <span className="hidden sm:block text-sm text-blue-200">
                {user.full_name || user.email}
              </span>
            )}
            <button
              onClick={() => { logout(); navigate('/login'); }}
              className="flex items-center gap-1 text-sm text-blue-200 hover:text-white transition-colors"
              title="Logout"
            >
              <LogOut size={15} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
