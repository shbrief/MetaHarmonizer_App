import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';
import type { Role } from '../api/types';
import { LoadingBlock } from './ui/Feedback';
import { EmptyState } from './ui/Feedback';
import { ShieldAlert } from 'lucide-react';

export default function ProtectedRoute({
  children,
  role,
}: {
  children: ReactNode;
  role?: Role;
}) {
  const { isAuthenticated, initializing, hasRole } = useAuth();
  const location = useLocation();

  if (initializing) {
    return <LoadingBlock label="Restoring your session…" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (role && !hasRole(role)) {
    return (
      <EmptyState
        icon={<ShieldAlert className="h-6 w-6 text-rose-500" />}
        title="Access restricted"
        description={`This area requires the ${role} role. Ask an administrator if you need access.`}
      />
    );
  }

  return <>{children}</>;
}
