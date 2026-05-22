// JARVIS App — Entry point
// Provider order matters:
//   QueryClientProvider → BrandProvider → BrowserRouter → AuthProvider → App
// BrowserRouter wraps AuthProvider so useNavigate works inside logout().
// Toaster lives at root so all pages can fire toast notifications.
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { queryClient } from '@/lib/queryClient';
import { BrandProvider } from '@/contexts/BrandContext';
import { AuthProvider } from '@/contexts/AuthContext';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrandProvider>
        <BrowserRouter>
          <AuthProvider>
            <App />
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 3500,
                style: { borderRadius: '10px', fontSize: '14px' },
              }}
            />
          </AuthProvider>
        </BrowserRouter>
      </BrandProvider>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  </React.StrictMode>
);
