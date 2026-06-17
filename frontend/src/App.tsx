import { Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom';
import { Upload, Table2, BarChart3, Download, Microscope, Shield } from 'lucide-react';
import { lazy, Suspense, type ReactNode } from 'react';
import Brand from './components/Brand';
import UserMenu from './components/UserMenu';
import ProtectedRoute from './components/ProtectedRoute';
import { LoadingBlock } from './components/ui/Feedback';
import { useAuth } from './context/AuthContext';

// Eager: tiny entry pages. Lazy: heavier feature pages (code-split per route).
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
const UploadPage = lazy(() => import('./pages/UploadPage'));
const MappingReview = lazy(() => import('./pages/MappingReview'));
const OntologyReview = lazy(() => import('./pages/OntologyReview'));
const QualityDashboard = lazy(() => import('./pages/QualityDashboard'));
const ExportPage = lazy(() => import('./pages/ExportPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));

const NAV_ITEMS = [
  { to: '/', icon: Upload, label: 'Upload', end: true },
  { to: '/review', icon: Table2, label: 'Mapping Review', end: false },
  { to: '/ontology', icon: Microscope, label: 'Ontology', end: false },
  { to: '/quality', icon: BarChart3, label: 'Quality', end: false },
  { to: '/export', icon: Download, label: 'Export', end: false },
];

function TopNav() {
  const { hasRole } = useAuth();
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Brand />

        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
          {hasRole('admin') && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
            >
              <Shield className="h-4 w-4" />
              Admin
            </NavLink>
          )}
        </nav>

        <UserMenu />
      </div>

      {/* Mobile nav */}
      <nav className="flex items-center gap-1 overflow-x-auto border-t border-slate-100 px-3 py-2 md:hidden">
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                isActive ? 'bg-primary-50 text-primary-700' : 'text-slate-600'
              }`
            }
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}

function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <TopNav />
      <main className="mx-auto w-full max-w-7xl flex-1 animate-fade-in px-4 py-8 sm:px-6 lg:px-8">
        <Suspense fallback={<LoadingBlock />}>{children}</Suspense>
      </main>
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        MetaHarmonizer Dashboard · Biomedical Metadata Harmonization · cBioPortal Compatible
      </footer>
    </div>
  );
}

/** Wrap an authenticated, shell-rendered page. */
function Shell({ children, role }: { children: ReactNode; role?: 'admin' | 'curator' }) {
  return (
    <ProtectedRoute role={role}>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

/** Redirect authenticated users away from login/register. */
function PublicOnly({ children }: { children: ReactNode }) {
  const { isAuthenticated, initializing } = useAuth();
  const location = useLocation();
  if (initializing) return null;
  if (isAuthenticated) {
    const from = (location.state as { from?: string } | null)?.from ?? '/';
    return <Navigate to={from} replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />

      <Route path="/" element={<Shell><UploadPage /></Shell>} />
      <Route path="/review" element={<Shell><MappingReview /></Shell>} />
      <Route path="/review/:studyId" element={<Shell><MappingReview /></Shell>} />
      <Route path="/ontology" element={<Shell><OntologyReview /></Shell>} />
      <Route path="/ontology/:studyId" element={<Shell><OntologyReview /></Shell>} />
      <Route path="/quality" element={<Shell><QualityDashboard /></Shell>} />
      <Route path="/quality/:studyId" element={<Shell><QualityDashboard /></Shell>} />
      <Route path="/export" element={<Shell><ExportPage /></Shell>} />
      <Route path="/export/:studyId" element={<Shell><ExportPage /></Shell>} />
      <Route path="/profile" element={<Shell><ProfilePage /></Shell>} />
      <Route path="/admin" element={<Shell role="admin"><AdminPage /></Shell>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
