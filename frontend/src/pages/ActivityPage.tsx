import { useMemo, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import {
  Activity,
  Check,
  X,
  Pencil,
  Layers,
  Sparkles,
  Trash2,
  CircleCheck,
  ShieldCheck,
  UserCog,
  Power,
  LogOut,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { queryAudit } from '../api/client';
import type { AuditEvent } from '../api/types';
import PageHeader from '../components/ui/PageHeader';
import { Card, CardBody } from '../components/ui/Card';
import { EmptyState, LoadingBlock } from '../components/ui/Feedback';

/** Human-readable verb + icon per audit action. */
const ACTION_META: Record<string, { verb: string; icon: ReactNode; tone: string }> = {
  accept: { verb: 'accepted a mapping', icon: <Check className="h-4 w-4" />, tone: 'text-emerald-600 bg-emerald-50' },
  reject: { verb: 'rejected a mapping', icon: <X className="h-4 w-4" />, tone: 'text-rose-600 bg-rose-50' },
  edit: { verb: 'edited a mapping', icon: <Pencil className="h-4 w-4" />, tone: 'text-amber-600 bg-amber-50' },
  batch_accepted: { verb: 'batch-accepted mappings', icon: <Layers className="h-4 w-4" />, tone: 'text-emerald-600 bg-emerald-50' },
  batch_rejected: { verb: 'batch-rejected mappings', icon: <Layers className="h-4 w-4" />, tone: 'text-rose-600 bg-rose-50' },
  llm_rematch: { verb: 'ran an LLM rematch', icon: <Sparkles className="h-4 w-4" />, tone: 'text-purple-600 bg-purple-50' },
  onto_accept: { verb: 'accepted an ontology term', icon: <Check className="h-4 w-4" />, tone: 'text-emerald-600 bg-emerald-50' },
  onto_reject: { verb: 'rejected an ontology term', icon: <X className="h-4 w-4" />, tone: 'text-rose-600 bg-rose-50' },
  onto_edit: { verb: 'edited an ontology term', icon: <Pencil className="h-4 w-4" />, tone: 'text-amber-600 bg-amber-50' },
  study_delete: { verb: 'deleted a study', icon: <Trash2 className="h-4 w-4" />, tone: 'text-rose-600 bg-rose-50' },
  study_complete: { verb: 'completed a study', icon: <CircleCheck className="h-4 w-4" />, tone: 'text-emerald-600 bg-emerald-50' },
  admin_set_role: { verb: 'changed a user role', icon: <UserCog className="h-4 w-4" />, tone: 'text-indigo-600 bg-indigo-50' },
  admin_approve_request: { verb: 'approved an admin request', icon: <ShieldCheck className="h-4 w-4" />, tone: 'text-indigo-600 bg-indigo-50' },
  admin_reject_request: { verb: 'denied an admin request', icon: <ShieldCheck className="h-4 w-4" />, tone: 'text-slate-600 bg-slate-100' },
  admin_set_active: { verb: 'changed account status', icon: <Power className="h-4 w-4" />, tone: 'text-amber-600 bg-amber-50' },
  admin_force_logout: { verb: 'forced a sign-out', icon: <LogOut className="h-4 w-4" />, tone: 'text-amber-600 bg-amber-50' },
};

const ACTION_OPTIONS = Object.keys(ACTION_META);

function meta(action: string) {
  return (
    ACTION_META[action] ?? {
      verb: action,
      icon: <Activity className="h-4 w-4" />,
      tone: 'text-slate-600 bg-slate-100',
    }
  );
}

function who(e: AuditEvent): string {
  return e.details?.curator ?? (e.actor_id != null ? `User #${e.actor_id}` : 'System');
}

function dayLabel(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const yest = new Date();
  yest.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yest.toDateString()) return 'Yesterday';
  return d.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export default function ActivityPage() {
  const [action, setAction] = useState('');
  const [studyId, setStudyId] = useState('');
  const [actorId, setActorId] = useState('');

  const filters = {
    action: action || undefined,
    study_id: studyId.trim() || undefined,
    actor_id: actorId.trim() ? Number(actorId.trim()) : undefined,
  };

  const query = useInfiniteQuery({
    queryKey: ['audit', filters],
    queryFn: ({ pageParam }) => queryAudit({ ...filters, cursor: pageParam, limit: 50 }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  });

  const events = useMemo(
    () => query.data?.pages.flatMap((p) => p.items) ?? [],
    [query.data],
  );

  // Group events by day for readable scanning.
  const groups = useMemo(() => {
    const map = new Map<string, AuditEvent[]>();
    for (const e of events) {
      const key = dayLabel(e.created_at);
      const list = map.get(key) ?? [];
      list.push(e);
      map.set(key, list);
    }
    return Array.from(map.entries());
  }, [events]);

  const clearFilters = () => {
    setAction('');
    setStudyId('');
    setActorId('');
  };
  const hasFilters = !!(action || studyId || actorId);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Activity log"
        description="Every curation and admin decision across the system — who did what, when, and to which study."
      />

      {/* Filters */}
      <Card>
        <CardBody className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            Action
            <select value={action} onChange={(e) => setAction(e.target.value)} className="field !py-2">
              <option value="">All actions</option>
              {ACTION_OPTIONS.map((a) => (
                <option key={a} value={a}>
                  {meta(a).verb}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            Study ID
            <input
              value={studyId}
              onChange={(e) => setStudyId(e.target.value)}
              placeholder="e.g. new_meta_1a2b"
              className="field !py-2"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
            User ID
            <input
              value={actorId}
              onChange={(e) => setActorId(e.target.value.replace(/[^0-9]/g, ''))}
              placeholder="numeric"
              className="field !w-28 !py-2"
            />
          </label>
          {hasFilters && (
            <button onClick={clearFilters} className="btn btn-sm border border-slate-200 text-slate-600 hover:bg-slate-50">
              Clear
            </button>
          )}
        </CardBody>
      </Card>

      {/* Feed */}
      {query.isLoading ? (
        <LoadingBlock label="Loading activity…" />
      ) : events.length === 0 ? (
        <EmptyState
          icon={<Activity className="h-6 w-6" />}
          title="No activity"
          description={hasFilters ? 'No events match these filters.' : 'Decisions will appear here as curators work.'}
        />
      ) : (
        <div className="space-y-6">
          {groups.map(([day, items]) => (
            <div key={day}>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">{day}</h3>
              <Card>
                <ul className="divide-y divide-slate-100">
                  {items.map((e) => {
                    const m = meta(e.action);
                    return (
                      <li key={e.id} className="flex items-center gap-3 px-4 py-3">
                        <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${m.tone}`}>
                          {m.icon}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-slate-800">
                            <span className="font-semibold">{who(e)}</span> {m.verb}
                            {e.new_value && <span className="text-slate-500"> · {e.new_value}</span>}
                          </p>
                          <p className="text-xs text-slate-400">
                            {e.study_id ? `Study ${e.study_id} · ` : ''}
                            {timeLabel(e.created_at)}
                          </p>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </Card>
            </div>
          ))}

          {query.hasNextPage && (
            <div className="flex justify-center">
              <button
                onClick={() => query.fetchNextPage()}
                disabled={query.isFetchingNextPage}
                className="btn btn-sm border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              >
                {query.isFetchingNextPage ? 'Loading…' : 'Load more'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
