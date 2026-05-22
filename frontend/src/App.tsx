// Universal App Router v1.0.0
// Locked UNIVERSAL template — works for ANY gig type.
// Provides: Login, Register, Dashboard, NotFound + protected layout.
// Gig-specific routes are added by gig-specific App.tsx overrides.
// If no gig override exists, this generic router handles everything.

import { Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import ProtectedRoute from '@/components/ProtectedRoute';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import Home from '@/pages/Home';
import NotFound from '@/pages/NotFound';
import Dashboard from '@/pages/Dashboard';
import CompanyPage from '@/pages/CompanyPage';
import ContactPage from '@/pages/ContactPage';
import ContactsPage from '@/pages/ContactsPage';
import CountyPage from '@/pages/CountyPage';
import CountysPage from '@/pages/CountysPage';
import NotificationPage from '@/pages/NotificationPage';
import OrderPage from '@/pages/OrderPage';
import RateBracketPage from '@/pages/RateBracketPage';
import RateBracketsPage from '@/pages/RateBracketsPage';
import RateTablePage from '@/pages/RateTablePage';
import ReissueDiscountPage from '@/pages/ReissueDiscountPage';
import ReissueDiscountsPage from '@/pages/ReissueDiscountsPage';
import SavedSheetPage from '@/pages/SavedSheetPage';
import SavedSheetsExportPage from '@/pages/SavedSheetsExportPage';
import CalculatorPage from '@/pages/CalculatorPage';

export default function App() {
  return (
    <Routes>
      {/* Public — no auth required */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected (active account required) */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="companies" element={<CompanyPage />} />
        <Route path="contact" element={<ContactPage />} />
        <Route path="contacts" element={<ContactsPage />} />
        <Route path="county" element={<CountyPage />} />
        <Route path="countys" element={<CountysPage />} />
        <Route path="notifications" element={<NotificationPage />} />
        <Route path="orders" element={<OrderPage />} />
        <Route path="rate-brackets" element={<RateBracketPage />} />
        <Route path="rate-brackets-list" element={<RateBracketsPage />} />
        <Route path="rate-tables" element={<RateTablePage />} />
        <Route path="reissue-discounts" element={<ReissueDiscountPage />} />
        <Route path="reissue-discounts-list" element={<ReissueDiscountsPage />} />
        <Route path="saved-sheets" element={<SavedSheetPage />} />
        <Route path="saved-sheets-export" element={<SavedSheetsExportPage />} />
        <Route path="calculators" element={<CalculatorPage />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
