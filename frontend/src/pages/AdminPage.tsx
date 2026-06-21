import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { Shield, Users, LogOut, Ban, CheckCircle2, ShieldCheck, X, MailWarning, Layers, Upload, CheckCheck } from 'lucide-react';
import { toast } from 'sonner';
import PageHeader from '../components/ui/PageHeader';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { LoadingBlock, EmptyState } from '../components/ui/Feedback';
import { useAuth } from '../context/AuthContext';
import {
  adminApproveAdmin,
  adminForceLogout,
  adminListUsers,
  adminListSchemaVersions,
  adminPromoteSchemaVersion,
  adminRejectAdmin,
  adminSetActive,
  adminSetRole,
  adminUploadSchemaVersion,
} from '../api/auth';
import type { Role, User } from '../api/types';

const ROLES: Role[] = ['curator', 'admin'];

export default function AdminPage() {
  const { user: me } = useAuth();
  const qc = useQueryClient();

  const users = useQuery({ queryKey: ['admin', 'users'], queryFn: adminListUsers });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin', 'users'] });

  const roleM = useMutation({
    mutationFn: ({ id, role }: { id: number; role: Role }) => adminSetRole(id, role),
    onSuccess: (u) => {
      invalidate();
      toast.success(`${u.email} is now ${u.role}`);
    },
    onError: (e: any) => toast.error(e?.message ?? 'Could not change role'),
  });

  const activeM = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => adminSetActive(id, isActive),
    onSuccess: (u) => {
      invalidate();
      toast.success(`${u.email} ${u.is_active ? 'enabled' : 'disabled'}`);
    },
    onError: (e: any) => toast.error(e?.message ?? 'Could not update account'),
  });

  const logoutM = useMutation({
    mutationFn: adminForceLogout,
    onSuccess: () => toast.success('All sessions revoked'),
    onError: () => toast.error('Could not force sign-out'),
  });

  const approveM = useMutation({
    mutationFn: adminApproveAdmin,
    onSuccess: (u) => {
      invalidate();
      toast.success(`${u.email} is now an admin`);
    },
    onError: (e: any) => toast.error(e?.message ?? 'Could not approve request'),
  });

  const rejectM = useMutation({
    mutationFn: adminRejectAdmin,
    onSuccess: (u) => {
      invalidate();
      toast(`Admin request for ${u.email} declined`);
    },
    onError: (e: any) => toast.error(e?.message ?? 'Could not decline request'),
  });

  const stats = computeStats(users.data ?? []);
  const pendingRequests = (users.data ?? []).filter((u) => u.admin_requested && u.role !== 'admin');

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageHeader
        title="Admin console"
        description="Manage team members, roles, and access."
        actions={
          <Badge tone="primary">
            <Shield className="h-3.5 w-3.5" />
            Admin only
          </Badge>
        }
      />

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Total users" value={stats.total} />
        <Stat label="Admins" value={stats.admin} tone="text-primary-600" />
        <Stat label="Curators" value={stats.curator} tone="text-accent-600" />
        <Stat label="Disabled" value={stats.disabled} tone="text-rose-600" />
      </div>

      {/* Pending admin-access requests */}
      {pendingRequests.length > 0 && (
        <Card className="overflow-hidden border-amber-200">
          <div className="flex items-center gap-2 border-b border-amber-100 bg-amber-50/70 px-5 py-3">
            <ShieldCheck className="h-4 w-4 text-amber-600" />
            <h3 className="text-sm font-semibold text-amber-800">
              Admin access requests
              <span className="ml-1.5 font-normal text-amber-600">({pendingRequests.length})</span>
            </h3>
          </div>
          <ul className="divide-y divide-slate-100">
            {pendingRequests.map((u) => (
              <li key={u.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-800">{u.name || u.email}</p>
                  <p className="truncate text-xs text-slate-500">{u.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                    loading={approveM.isPending && approveM.variables === u.id}
                    onClick={() => approveM.mutate(u.id)}
                  >
                    Approve
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-rose-600 hover:bg-rose-50"
                    icon={<X className="h-3.5 w-3.5" />}
                    loading={rejectM.isPending && rejectM.variables === u.id}
                    onClick={() => rejectM.mutate(u.id)}
                  >
                    Decline
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="overflow-hidden">
        {users.isLoading ? (
          <LoadingBlock label="Loading users…" />
        ) : !users.data?.length ? (
          <EmptyState icon={<Users className="h-6 w-6" />} title="No users found" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/80 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-3">User</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.data.map((u) => {
                  const isSelf = u.id === me?.id;
                  return (
                    <tr key={u.id} className="hover:bg-slate-50/60">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <span className="grid h-9 w-9 place-items-center rounded-xl bg-slate-100 text-xs font-bold text-slate-600">
                            {(u.name || u.email).slice(0, 2).toUpperCase()}
                          </span>
                          <div className="min-w-0">
                            <p className="truncate font-medium text-slate-800">
                              {u.name || '—'}
                              {isSelf && <span className="ml-1.5 text-xs text-slate-400">(you)</span>}
                            </p>
                            <p className="truncate text-xs text-slate-500">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <select
                          value={u.role}
                          disabled={isSelf || roleM.isPending}
                          onChange={(e) => roleM.mutate({ id: u.id, role: e.target.value as Role })}
                          className="field !w-auto !py-1.5 text-xs disabled:opacity-60"
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-5 py-3">
                        {!u.is_active ? (
                          <Badge tone="rose">
                            <Ban className="h-3.5 w-3.5" />
                            Disabled
                          </Badge>
                        ) : !u.email_verified ? (
                          <Badge tone="amber">
                            <MailWarning className="h-3.5 w-3.5" />
                            Unverified
                          </Badge>
                        ) : (
                          <Badge tone="green">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Active
                          </Badge>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<LogOut className="h-3.5 w-3.5" />}
                            loading={logoutM.isPending && logoutM.variables === u.id}
                            onClick={() => logoutM.mutate(u.id)}
                          >
                            Force sign-out
                          </Button>
                          <Button
                            variant={u.is_active ? 'ghost' : 'secondary'}
                            size="sm"
                            disabled={isSelf}
                            icon={u.is_active ? <Ban className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                            className={u.is_active ? 'text-rose-600 hover:bg-rose-50' : ''}
                            loading={activeM.isPending && activeM.variables?.id === u.id}
                            onClick={() => activeM.mutate({ id: u.id, isActive: !u.is_active })}
                          >
                            {u.is_active ? 'Disable' : 'Enable'}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <SchemaVersionsCard />
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tone ?? 'text-slate-900'}`}>{value}</p>
    </Card>
  );
}

function computeStats(users: User[]) {
  return {
    total: users.length,
    admin: users.filter((u) => u.role === 'admin').length,
    curator: users.filter((u) => u.role === 'curator').length,
    disabled: users.filter((u) => !u.is_active).length,
  };
}

function SchemaVersionsCard() {
  const qc = useQueryClient();
  const versions = useQuery({ queryKey: ['admin', 'schema-versions'], queryFn: adminListSchemaVersions });
  const fileRef = useRef<HTMLInputElement>(null);
  const [label, setLabel] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const invalidate = () => qc.invalidateQueries({ queryKey: ['admin', 'schema-versions'] });

  const uploadM = useMutation({
    mutationFn: () => adminUploadSchemaVersion(label.trim(), file!, true),
    onSuccess: (v) => {
      invalidate();
      toast.success(`Schema ${v.label} uploaded and promoted`);
      setLabel('');
      setFile(null);
      if (fileRef.current) fileRef.current.value = '';
    },
    onError: (e: any) => toast.error(e?.message ?? 'Could not upload schema version'),
  });

  const promoteM = useMutation({
    mutationFn: adminPromoteSchemaVersion,
    onSuccess: (v) => {
      invalidate();
      toast.success(`Schema ${v.label} is now current`);
    },
    onError: (e: any) => toast.error(e?.message ?? 'Could not promote version'),
  });

  return (
    <Card>
      <CardHeader
        icon={<Layers className="h-4 w-4" />}
        title="Schema versions"
        description="The curated-fields schema new studies map against. New uploads are new versions — existing studies stay pinned."
      />
      <CardBody className="space-y-4">
        {/* Upload form */}
        <form
          className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (label.trim() && file) uploadM.mutate();
          }}
        >
          <div>
            <label htmlFor="schema-label" className="block text-xs font-medium text-slate-500">
              Version label
            </label>
            <input
              id="schema-label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. v2"
              className="mt-1 w-28 rounded border border-slate-200 px-2 py-1.5 text-sm focus:border-primary-400 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="schema-file" className="block text-xs font-medium text-slate-500">
              Curated-fields CSV
            </label>
            <input
              id="schema-file"
              ref={fileRef}
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="mt-1 text-sm file:mr-2 file:rounded file:border-0 file:bg-primary-50 file:px-2 file:py-1 file:text-primary-700"
            />
          </div>
          <Button
            type="submit"
            loading={uploadM.isPending}
            disabled={!label.trim() || !file}
            icon={<Upload className="h-4 w-4" />}
          >
            Upload &amp; promote
          </Button>
        </form>

        {/* Versions list */}
        {versions.isLoading ? (
          <LoadingBlock label="Loading schema versions…" />
        ) : !versions.data?.length ? (
          <EmptyState title="No schema versions yet" />
        ) : (
          <ul className="divide-y divide-slate-100">
            {versions.data.map((v) => (
              <li key={v.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-medium text-slate-800">{v.label}</span>
                  {v.is_current ? (
                    <Badge tone="green">
                      <CheckCheck className="h-3.5 w-3.5" />
                      Current
                    </Badge>
                  ) : null}
                  <span className="text-xs text-slate-400">
                    {new Date(v.created_at).toLocaleDateString()}
                  </span>
                </div>
                {!v.is_current && (
                  <Button
                    variant="secondary"
                    size="sm"
                    loading={promoteM.isPending && promoteM.variables === v.id}
                    onClick={() => promoteM.mutate(v.id)}
                  >
                    Make current
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
