import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Check,
  Loader2,
  Pencil,
  Search,
  X,
  ChevronDown,
  ChevronRight,
  Tags,
  CircleCheck,
  Clock,
  HelpCircle,
  Plus,
} from 'lucide-react';
import {
  acceptOntologyMapping,
  editOntologyMapping,
  getOntologyMappings,
  rejectOntologyMapping,
  searchOntology,
} from '../api/client';
import { useStudies } from '../hooks/queries';
import ConfidenceBadge from '../components/ConfidenceBadge';
import StatusBadge from '../components/StatusBadge';
import PageHeader from '../components/ui/PageHeader';
import StudyPicker, { StudySelect } from '../components/StudyPicker';
import StudyGate, { isStudyReady } from '../components/StudyGate';
import { Card, CardBody } from '../components/ui/Card';
import type { OntologyMapping, OntologySearchResult } from '../api/types';

interface EditState { id: number; term: string; ontId: string; raw?: string }
type StatusFilter = 'all' | 'pending' | 'accepted' | 'rejected';

const hasTerm = (m: OntologyMapping) => !!(m.curator_term ?? m.ontology_term);

export default function OntologyReview() {
  const { studyId } = useParams<{ studyId: string }>();
  const navigate = useNavigate();
  const { data: studies, isLoading: studiesLoading } = useStudies();

  const [selectedId, setSelectedId] = useState<string | null>(studyId ?? null);
  const [ontoMappings, setOntoMappings] = useState<OntologyMapping[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<Record<number, boolean>>({});
  const [editState, setEditState] = useState<EditState | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [showUnmatched, setShowUnmatched] = useState(false);

  // Search (lives inside the edit modal)
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<OntologySearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    setSelectedId(studyId ?? null);
  }, [studyId]);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    getOntologyMappings(selectedId)
      .then(setOntoMappings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedId]);

  const patch = (updated: OntologyMapping) =>
    setOntoMappings((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));

  const handleAccept = async (id: number) => {
    setBusy((b) => ({ ...b, [id]: true }));
    try { patch(await acceptOntologyMapping(id)); } catch { /* ignore */ }
    finally { setBusy((b) => ({ ...b, [id]: false })); }
  };

  const handleReject = async (id: number) => {
    setBusy((b) => ({ ...b, [id]: true }));
    try { patch(await rejectOntologyMapping(id)); } catch { /* ignore */ }
    finally { setBusy((b) => ({ ...b, [id]: false })); }
  };

  const handleEditSave = async () => {
    if (!editState || !editState.term.trim()) return;
    setBusy((b) => ({ ...b, [editState.id]: true }));
    try {
      patch(await editOntologyMapping(editState.id, editState.term.trim(), editState.ontId.trim()));
      setEditState(null);
      setSearchResults([]);
      setSearchQuery('');
    } catch { /* ignore */ }
    finally { setBusy((b) => ({ ...b, [editState!.id]: false })); }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try { setSearchResults(await searchOntology(searchQuery)); }
    catch { setSearchResults([]); }
    finally { setSearching(false); }
  };

  const handleStudyChange = (id: string) => {
    setSelectedId(id);
    navigate(`/ontology/${id}`, { replace: true });
  };

  // ── Split matched (has a candidate ontology term — actionable) from
  //    unmatched (free-text / identifiers with no ontology equivalent — noise).
  const { matched, unmatched } = useMemo(() => {
    const m: OntologyMapping[] = [];
    const u: OntologyMapping[] = [];
    for (const om of ontoMappings) (hasTerm(om) ? m : u).push(om);
    return { matched: m, unmatched: u };
  }, [ontoMappings]);

  const stats = useMemo(() => ({
    mapped: matched.length,
    accepted: matched.filter((m) => m.status === 'accepted').length,
    pending: matched.filter((m) => m.status === 'pending').length,
    unmatched: unmatched.length,
  }), [matched, unmatched]);

  // Matched, filtered by status, grouped by field.
  const groupedMatched = useMemo(() => {
    const rows = statusFilter === 'all' ? matched : matched.filter((m) => m.status === statusFilter);
    const g: Record<string, OntologyMapping[]> = {};
    for (const m of rows) (g[m.field_name] ??= []).push(m);
    return g;
  }, [matched, statusFilter]);

  // Unmatched grouped by field (for the collapsed explainer).
  const groupedUnmatched = useMemo(() => {
    const g: Record<string, OntologyMapping[]> = {};
    for (const m of unmatched) (g[m.field_name] ??= []).push(m);
    return g;
  }, [unmatched]);

  if (!selectedId) {
    return (
      <StudyPicker
        title="Ontology review"
        description="Pick a study to review and curate ontology value mappings."
        studies={studies}
        loading={studiesLoading}
        basePath="/ontology"
      />
    );
  }

  const selectedStudy = studies?.find((s) => s.id === selectedId);
  if (selectedStudy && !isStudyReady(selectedStudy.status)) {
    return <StudyGate study={selectedStudy} title="Ontology review" />;
  }

  const matchedFields = Object.keys(groupedMatched);

  return (
    <div className="space-y-6">
      {/* Edit Modal (with embedded search) */}
      {editState && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setEditState(null)}>
          <div className="w-full max-w-lg space-y-4 rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-semibold text-slate-800">Set ontology term</h3>
            {editState.raw && (
              <p className="text-xs text-slate-500">
                Assigning a term to <code className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-700">{editState.raw}</code>
              </p>
            )}
            <div className="space-y-2">
              <label className="text-xs text-slate-500">Term name</label>
              <input
                autoFocus
                value={editState.term}
                onChange={(e) => setEditState({ ...editState, term: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && handleEditSave()}
                placeholder="e.g. Male"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-slate-500">Ontology ID (optional — auto-resolved if blank)</label>
              <input
                value={editState.ontId}
                onChange={(e) => setEditState({ ...editState, ontId: e.target.value })}
                placeholder="e.g. NCIT:C20197"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
              />
            </div>

            {/* Search panel */}
            <div className="rounded-lg border border-slate-100 bg-slate-50/60 p-3">
              <div className="flex gap-2">
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search NCIT, UBERON…"
                  className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
                <button onClick={handleSearch} disabled={searching} className="rounded-lg bg-primary-600 p-2 text-white hover:bg-primary-700">
                  {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                </button>
              </div>
              {searchResults.length > 0 && (
                <ul className="mt-3 max-h-56 space-y-2 overflow-y-auto">
                  {searchResults.map((r, i) => (
                    <li
                      key={i}
                      onClick={() => setEditState({ ...editState, term: r.term, ontId: r.ontology_id })}
                      className="cursor-pointer rounded-lg border border-slate-100 bg-white p-2 text-xs hover:border-primary-300 hover:bg-primary-50"
                    >
                      <div className="font-medium text-slate-900">{r.term}</div>
                      <div className="mt-0.5 flex items-center gap-2">
                        <span className="font-mono text-slate-500">{r.ontology_id}</span>
                        <span className="text-slate-400">{r.ontology}</span>
                        <ConfidenceBadge score={r.score} size="sm" />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="flex justify-end gap-2">
              <button onClick={() => setEditState(null)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">
                Cancel
              </button>
              <button
                disabled={!editState.term.trim() || busy[editState.id]}
                onClick={handleEditSave}
                className="flex items-center gap-1 rounded-lg bg-primary-600 px-3 py-1.5 text-sm text-white hover:bg-primary-700 disabled:opacity-50"
              >
                {busy[editState.id] ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      <PageHeader
        title="Ontology review"
        description="Curate the controlled-vocabulary terms the engine assigned to each categorical value."
        actions={<StudySelect studies={studies} value={selectedId} onChange={handleStudyChange} />}
      />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard icon={<Tags className="h-4 w-4" />} label="Mapped values" value={stats.mapped} tone="primary" />
            <StatCard icon={<Clock className="h-4 w-4" />} label="Pending review" value={stats.pending} tone="amber" />
            <StatCard icon={<CircleCheck className="h-4 w-4" />} label="Accepted" value={stats.accepted} tone="emerald" />
            <StatCard icon={<HelpCircle className="h-4 w-4" />} label="No ontology match" value={stats.unmatched} tone="slate" />
          </div>

          {stats.mapped === 0 ? (
            <Card>
              <CardBody className="py-12 text-center text-slate-400">
                No values in this study mapped to an ontology term.
              </CardBody>
            </Card>
          ) : (
            <>
              {/* Status filter */}
              <div className="flex flex-wrap items-center gap-2">
                {(['all', 'pending', 'accepted', 'rejected'] as StatusFilter[]).map((f) => (
                  <button
                    key={f}
                    onClick={() => setStatusFilter(f)}
                    className={`chip capitalize ${statusFilter === f ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                  >
                    {f}
                  </button>
                ))}
              </div>

              {/* Matched, grouped by field */}
              {matchedFields.length === 0 ? (
                <Card>
                  <CardBody className="py-8 text-center text-sm text-slate-400">
                    No {statusFilter !== 'all' ? statusFilter : ''} values to show.
                  </CardBody>
                </Card>
              ) : (
                <div className="space-y-4">
                  {matchedFields.map((field) => (
                    <div key={field} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                      <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 px-4 py-2.5">
                        <h3 className="text-sm font-semibold text-slate-800">{field}</h3>
                        <span className="text-xs text-slate-400">
                          {groupedMatched[field].length} value{groupedMatched[field].length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <ul className="divide-y divide-slate-100">
                        {groupedMatched[field].map((om) => {
                          const isBusy = !!busy[om.id];
                          const term = om.curator_term ?? om.ontology_term;
                          const oid = om.curator_id ?? om.ontology_id;
                          return (
                            <li key={om.id} className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-2.5 hover:bg-slate-50">
                              {/* raw → term */}
                              <div className="flex min-w-0 flex-1 items-center gap-2">
                                <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-700">{om.raw_value}</code>
                                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-300" />
                                <span className="truncate text-sm font-medium text-slate-900">{term}</span>
                                {om.curator_term && <span className="text-[10px] text-amber-600">(edited)</span>}
                                {oid && <span className="truncate font-mono text-[11px] text-slate-400">{oid}</span>}
                              </div>
                              <ConfidenceBadge score={om.confidence_score} size="sm" />
                              <StatusBadge status={om.status} />
                              <div className="flex items-center gap-1">
                                {isBusy ? (
                                  <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                                ) : (
                                  <>
                                    {om.status !== 'accepted' && (
                                      <button title="Accept" onClick={() => handleAccept(om.id)} className="rounded p-1 text-emerald-600 hover:bg-emerald-50">
                                        <Check className="h-3.5 w-3.5" />
                                      </button>
                                    )}
                                    {om.status !== 'rejected' && (
                                      <button title="Reject" onClick={() => handleReject(om.id)} className="rounded p-1 text-rose-500 hover:bg-rose-50">
                                        <X className="h-3.5 w-3.5" />
                                      </button>
                                    )}
                                    <button
                                      title="Edit term"
                                      onClick={() => setEditState({ id: om.id, term: term ?? '', ontId: oid ?? '', raw: om.raw_value })}
                                      className="rounded p-1 text-blue-500 hover:bg-blue-50"
                                    >
                                      <Pencil className="h-3.5 w-3.5" />
                                    </button>
                                  </>
                                )}
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Unmatched — collapsed explainer (free-text / identifiers) */}
          {stats.unmatched > 0 && (
            <Card>
              <button
                onClick={() => setShowUnmatched((s) => !s)}
                className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
              >
                <span className="flex items-center gap-2 text-sm font-medium text-slate-700">
                  {showUnmatched ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
                  {stats.unmatched.toLocaleString()} values had no ontology match
                </span>
                <span className="hidden text-xs text-slate-400 sm:inline">free-text or identifiers — no action needed</span>
              </button>
              {showUnmatched && (
                <CardBody className="space-y-3 border-t border-slate-100 pt-4">
                  <p className="text-xs text-slate-500">
                    These values didn’t match a controlled-vocabulary term (often sample IDs, study
                    names, or free text). Most need no action — but if one should have a term, click
                    it to assign one manually.
                  </p>
                  {Object.entries(groupedUnmatched).map(([field, items]) => (
                    <div key={field}>
                      <p className="mb-1 text-xs font-semibold text-slate-600">
                        {field} <span className="font-normal text-slate-400">· {items.length}</span>
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {items.slice(0, 40).map((m) => (
                          <button
                            key={m.id}
                            title="Assign an ontology term"
                            onClick={() => setEditState({ id: m.id, term: '', ontId: '', raw: m.raw_value })}
                            className="group inline-flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500 hover:bg-primary-50 hover:text-primary-700"
                          >
                            {m.raw_value}
                            <Plus className="h-2.5 w-2.5 opacity-0 transition group-hover:opacity-100" />
                          </button>
                        ))}
                        {items.length > 40 && (
                          <span className="px-1 py-0.5 text-[11px] text-slate-400">+{items.length - 40} more</span>
                        )}
                      </div>
                    </div>
                  ))}
                </CardBody>
              )}
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  tone: 'primary' | 'amber' | 'emerald' | 'slate';
}) {
  const tones: Record<string, string> = {
    primary: 'bg-primary-50 text-primary-700',
    amber: 'bg-amber-50 text-amber-700',
    emerald: 'bg-emerald-50 text-emerald-700',
    slate: 'bg-slate-100 text-slate-600',
  };
  return (
    <Card>
      <CardBody className="flex items-center gap-3 py-3">
        <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ${tones[tone]}`}>{icon}</span>
        <div className="min-w-0">
          <div className="text-lg font-bold text-slate-900">{value.toLocaleString()}</div>
          <div className="truncate text-xs text-slate-500">{label}</div>
        </div>
      </CardBody>
    </Card>
  );
}
