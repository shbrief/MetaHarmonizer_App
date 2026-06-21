import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import {
  Check,
  X,
  Pencil,
  ChevronDown,
  ChevronUp,
  Filter,
  ArrowUpDown,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Search,
} from 'lucide-react';
import { toast } from 'sonner';
import ConfidenceBadge from '../components/ConfidenceBadge';
import StageBadge from '../components/StageBadge';
import StatusBadge from '../components/StatusBadge';
import PageHeader from '../components/ui/PageHeader';
import StudyPicker from '../components/StudyPicker';
import StudyGate, { isStudyReady } from '../components/StudyGate';
import { useStudies } from '../hooks/queries';
import {
  getStudyMappings,
  acceptMapping,
  rejectMapping,
  editMapping,
  batchUpdateMappings,
  llmRematch,
} from '../api/client';
import { ApiError } from '../api/http';
import type { Mapping } from '../api/types';

type SortKey = 'raw_column' | 'confidence_score' | 'stage' | 'status';
type FilterStage = 'all' | 'stage1' | 'stage2' | 'stage3' | 'stage4' | 'invalid' | 'unmapped';
type FilterStatus = 'all' | 'pending' | 'accepted' | 'rejected';

// Stage display order + colours for the distribution bar (aligned with StageBadge).
const STAGE_ORDER = ['stage1', 'stage2', 'stage3', 'stage4', 'invalid', 'unmapped'] as const;
const STAGE_META: Record<string, { label: string; bar: string }> = {
  stage1: { label: 'S1 Dict/Fuzzy', bar: 'bg-blue-500' },
  stage2: { label: 'S2 Value/Ontology', bar: 'bg-indigo-500' },
  stage3: { label: 'S3 Semantic', bar: 'bg-purple-500' },
  stage4: { label: 'S4 LLM', bar: 'bg-orange-500' },
  invalid: { label: 'Invalid', bar: 'bg-red-500' },
  unmapped: { label: 'Unmapped', bar: 'bg-gray-400' },
};

export default function MappingReview() {
  const { studyId } = useParams<{ studyId: string }>();
  const { data: studies, isLoading: studiesLoading } = useStudies();

  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(studyId ?? null);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  // Filters — default to "pending" so curators see only actionable items.
  // Deep-links from the Quality dashboard can preset them via ?status= / ?stage=.
  const [searchParams] = useSearchParams();
  const initialStatus = (searchParams.get('status') as FilterStatus) || 'pending';
  const initialStage = (searchParams.get('stage') as FilterStage) || 'all';
  const [filterStage, setFilterStage] = useState<FilterStage>(initialStage);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>(initialStatus);
  const [sortKey, setSortKey] = useState<SortKey>('confidence_score');
  const [sortAsc, setSortAsc] = useState(false);
  const [search, setSearch] = useState('');

  // Keyboard navigation: index of the focused row within the filtered list.
  const [cursor, setCursor] = useState(0);
  const searchRef = React.useRef<HTMLInputElement>(null);

  // Edit modal
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editField, setEditField] = useState('');
  const [editNote, setEditNote] = useState('');

  // Keep the selected study in sync with the URL param (e.g. when the study
  // picker navigates from /review to /review/:studyId).
  useEffect(() => {
    setSelectedId(studyId ?? null);
  }, [studyId]);

  // Load mappings when study selected
  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    getStudyMappings(selectedId)
      .then(setMappings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedId]);

  const showToast = (message: string, type: 'success' | 'error' = 'success') =>
    type === 'success' ? toast.success(message) : toast.error(message);

  // Status filter

  // Filter + sort
  const filteredMappings = useMemo(() => {
    let result = [...mappings];
    if (filterStage !== 'all') result = result.filter((m) => m.stage === filterStage);
    if (filterStatus !== 'all') result = result.filter((m) => m.status === filterStatus);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter(
        (m) =>
          m.raw_column.toLowerCase().includes(q) ||
          (m.curator_field || m.matched_field || '').toLowerCase().includes(q),
      );
    }
    result.sort((a, b) => {
      let av: any = a[sortKey];
      let bv: any = b[sortKey];
      if (av === null) av = sortKey === 'confidence_score' ? -1 : '';
      if (bv === null) bv = sortKey === 'confidence_score' ? -1 : '';
      if (typeof av === 'string') return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortAsc ? av - bv : bv - av;
    });
    return result;
  }, [mappings, filterStage, filterStatus, sortKey, sortAsc, search]);

  // Per-stage counts for the distribution bar (full study, not the filtered view).
  const stageCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const m of mappings) {
      const key = m.stage ?? 'unmapped';
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, [mappings]);

  // Actions
  const updateMapping = useCallback(
    (updated: Mapping) => {
      setMappings((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
    },
    [],
  );

  const handleAccept = async (id: number) => {
    try {
      const m = await acceptMapping(id);
      updateMapping(m);
      showToast(`Accepted: ${m.raw_column} → ${m.curator_field || m.matched_field}`);
    } catch {
      showToast('Failed to accept mapping', 'error');
    }
  };
  const handleReject = async (id: number) => {
    try {
      const m = await rejectMapping(id);
      updateMapping(m);
      showToast(`Rejected: ${m.raw_column}`);
    } catch {
      showToast('Failed to reject mapping', 'error');
    }
  };
  const handleEditSubmit = async () => {
    if (editingId === null) return;
    try {
      const m = await editMapping(editingId, editField, editNote);
      updateMapping(m);
      showToast(`Edited: ${m.raw_column} → ${editField}`);
    } catch {
      showToast('Failed to edit mapping', 'error');
    }
    setEditingId(null);
    setEditField('');
    setEditNote('');
  };

  // 1-click: apply one of the engine's alternative suggestions as the field.
  const handleApplyAlternative = async (id: number, field: string) => {
    try {
      const m = await editMapping(id, field, 'Applied alternative suggestion');
      updateMapping(m);
      showToast(`Applied: ${m.raw_column} → ${field}`);
    } catch {
      showToast('Failed to apply alternative', 'error');
    }
  };

  // On-demand Stage-4 LLM rematch for a stuck column (needs GEMINI_API_KEY).
  const [llmBusyId, setLlmBusyId] = useState<number | null>(null);
  const [llmResults, setLlmResults] = useState<Record<number, { field: string; confidence: number; reasoning: string }[]>>({});
  const handleLlmRematch = async (id: number) => {
    setLlmBusyId(id);
    try {
      const suggestions = await llmRematch(id);
      setLlmResults((prev) => ({ ...prev, [id]: suggestions }));
      setExpandedRow(id);
      showToast(suggestions.length ? `LLM suggested ${suggestions.length} match(es)` : 'LLM returned no suggestions');
    } catch (err) {
      const msg =
        err instanceof ApiError && err.status === 503
          ? 'LLM matching is not configured on the server (set GEMINI_API_KEY).'
          : 'LLM rematch failed. Please try again.';
      showToast(msg, 'error');
    } finally {
      setLlmBusyId(null);
    }
  };

  const handleBatch = async (action: 'accepted' | 'rejected') => {
    if (selected.size === 0) return;
    try {
      await batchUpdateMappings([...selected], action);
      // Reload
      if (selectedId) {
        const fresh = await getStudyMappings(selectedId);
        setMappings(fresh);
      }
      showToast(`${action === 'accepted' ? 'Accepted' : 'Rejected'} ${selected.size} mappings`);
    } catch {
      showToast('Batch update failed', 'error');
    }
    setSelected(new Set());
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };
  const toggleSelectAll = () => {
    if (selected.size === filteredMappings.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredMappings.map((m) => m.id)));
    }
  };

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const openEdit = (m: Mapping) => {
    setEditingId(m.id);
    setEditField(m.curator_field || m.matched_field || '');
    setEditNote('');
  };

  // Keep the cursor within bounds when the filtered list changes.
  useEffect(() => {
    setCursor((c) => Math.min(Math.max(0, c), Math.max(0, filteredMappings.length - 1)));
  }, [filteredMappings.length]);

  // Keyboard shortcuts: j/k move, a/r accept/reject, e edit, x select, Enter
  // expand, / focus search. Ignored while typing in a field or a modal is open.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
      if (e.key === '/' && !typing) {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }
      if (typing || editingId !== null) return;
      const list = filteredMappings;
      if (!list.length) return;
      const cur = list[Math.min(cursor, list.length - 1)];
      switch (e.key) {
        case 'j':
          e.preventDefault();
          setCursor((c) => Math.min(c + 1, list.length - 1));
          break;
        case 'k':
          e.preventDefault();
          setCursor((c) => Math.max(c - 1, 0));
          break;
        case 'a':
          if (cur && cur.status !== 'accepted') { e.preventDefault(); handleAccept(cur.id); }
          break;
        case 'r':
          if (cur && cur.status !== 'rejected') { e.preventDefault(); handleReject(cur.id); }
          break;
        case 'e':
          if (cur) { e.preventDefault(); openEdit(cur); }
          break;
        case 'x':
          if (cur) { e.preventDefault(); toggleSelect(cur.id); }
          break;
        case 'Enter':
          if (cur) { e.preventDefault(); setExpandedRow((r) => (r === cur.id ? null : cur.id)); }
          break;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [filteredMappings, cursor, editingId]);

  // Scroll the focused row into view as the cursor moves.
  useEffect(() => {
    const el = document.querySelector(`[data-row-cursor="true"]`);
    el?.scrollIntoView({ block: 'nearest' });
  }, [cursor]);

  // No study selected
  if (!selectedId) {
    return (
      <StudyPicker
        title="Mapping review"
        description="Pick a study to review and curate column mappings."
        studies={studies}
        loading={studiesLoading}
        basePath="/review"
      />
    );
  }

  // Study selected but not yet harmonized → show a readiness gate instead of an
  // empty table (auto-resolves to the real page once processing completes).
  const selectedStudy = studies?.find((s) => s.id === selectedId);
  if (selectedStudy && !isStudyReady(selectedStudy.status)) {
    return <StudyGate study={selectedStudy} title="Mapping review" />;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <PageHeader
        title="Schema mapping review"
        actions={
          selected.size > 0 ? (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-600">{selected.size} selected</span>
              <button onClick={() => handleBatch('accepted')} className="btn bg-emerald-600 text-white btn-sm hover:bg-emerald-700">
                <Check className="h-3.5 w-3.5" />
                Accept all
              </button>
              <button onClick={() => handleBatch('rejected')} className="btn-danger btn-sm">
                <X className="h-3.5 w-3.5" />
                Reject all
              </button>
            </div>
          ) : undefined
        }
      />

      {/* Status Summary Tabs */}
      <div className="flex gap-2">
        {(['pending', 'accepted', 'rejected', 'all'] as FilterStatus[]).map((status) => {
          const count =
            status === 'all'
              ? mappings.length
              : mappings.filter((m) => m.status === status).length;
          const icons: Record<string, React.ReactNode> = {
            pending: <Clock className="w-3.5 h-3.5" />,
            accepted: <CheckCircle2 className="w-3.5 h-3.5" />,
            rejected: <XCircle className="w-3.5 h-3.5" />,
            all: null,
          };
          const colors: Record<string, string> = {
            pending: filterStatus === status ? 'bg-amber-100 text-amber-800 border-amber-300' : 'text-amber-700 hover:bg-amber-50',
            accepted: filterStatus === status ? 'bg-green-100 text-green-800 border-green-300' : 'text-green-700 hover:bg-green-50',
            rejected: filterStatus === status ? 'bg-red-100 text-red-800 border-red-300' : 'text-red-700 hover:bg-red-50',
            all: filterStatus === status ? 'bg-gray-200 text-gray-800 border-gray-400' : 'text-gray-600 hover:bg-gray-100',
          };
          return (
            <button
              key={status}
              onClick={() => {
                setFilterStatus(status);
                setSelected(new Set());
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${colors[status]}`}
            >
              {icons[status]}
              {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
              <span className="bg-white/60 text-xs px-1.5 py-0.5 rounded-full font-semibold ml-1">
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Stage distribution — at-a-glance breakdown, click a segment to filter */}
      {mappings.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500">Stage breakdown</span>
            {filterStage !== 'all' && (
              <button
                onClick={() => setFilterStage('all')}
                className="text-xs font-medium text-primary-600 hover:text-primary-700"
              >
                Clear
              </button>
            )}
          </div>
          <div className="flex h-2.5 overflow-hidden rounded-full bg-gray-100">
            {STAGE_ORDER.map((s) => {
              const count = stageCounts[s] ?? 0;
              if (!count) return null;
              const pct = (count / mappings.length) * 100;
              return (
                <button
                  key={s}
                  title={`${STAGE_META[s].label}: ${count}`}
                  onClick={() => setFilterStage(filterStage === s ? 'all' : (s as FilterStage))}
                  className={`${STAGE_META[s].bar} transition-opacity hover:opacity-80 ${
                    filterStage !== 'all' && filterStage !== s ? 'opacity-30' : ''
                  }`}
                  style={{ width: `${pct}%` }}
                />
              );
            })}
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
            {STAGE_ORDER.map((s) => {
              const count = stageCounts[s] ?? 0;
              if (!count) return null;
              return (
                <button
                  key={s}
                  onClick={() => setFilterStage(filterStage === s ? 'all' : (s as FilterStage))}
                  className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-900"
                >
                  <span className={`h-2 w-2 rounded-full ${STAGE_META[s].bar}`} />
                  {STAGE_META[s].label}
                  <span className="font-semibold">{count}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 bg-white border border-gray-200 rounded-xl p-3">
        <Filter className="w-4 h-4 text-gray-400" />
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-500">Stage:</label>
          <select
            value={filterStage}
            onChange={(e) => setFilterStage(e.target.value as FilterStage)}
            className="text-sm border border-gray-200 rounded px-2 py-1"
          >
            <option value="all">All</option>
            <option value="stage1">S1 Dict/Fuzzy</option>
            <option value="stage2">S2 Value/Ontology</option>
            <option value="stage3">S3 Semantic</option>
            <option value="stage4">S4 LLM</option>
            <option value="invalid">Invalid</option>
            <option value="unmapped">Unmapped</option>
          </select>
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
          <input
            ref={searchRef}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search columns…  ( / )"
            className="w-48 rounded border border-gray-200 py-1 pl-7 pr-2 text-sm focus:border-primary-400 focus:outline-none"
          />
        </div>
        <span className="text-xs text-gray-400 ml-auto">
          {filteredMappings.length} of {mappings.length} shown
        </span>
      </div>

      {/* Keyboard hint */}
      <p className="-mt-2 px-1 text-[11px] text-gray-400">
        Shortcuts: <kbd className="rounded bg-gray-100 px-1">j</kbd>/<kbd className="rounded bg-gray-100 px-1">k</kbd> move ·
        <kbd className="rounded bg-gray-100 px-1">a</kbd> accept · <kbd className="rounded bg-gray-100 px-1">r</kbd> reject ·
        <kbd className="rounded bg-gray-100 px-1">e</kbd> edit · <kbd className="rounded bg-gray-100 px-1">x</kbd> select ·
        <kbd className="rounded bg-gray-100 px-1">Enter</kbd> details · <kbd className="rounded bg-gray-100 px-1">/</kbd> search
      </p>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-3 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selected.size === filteredMappings.length && filteredMappings.length > 0}
                    onChange={toggleSelectAll}
                    className="rounded"
                  />
                </th>
                <SortableHeader label="Raw Column" sortKey="raw_column" current={sortKey} asc={sortAsc} onSort={toggleSort} />
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Matched Field
                </th>
                <SortableHeader label="Confidence" sortKey="confidence_score" current={sortKey} asc={sortAsc} onSort={toggleSort} />
                <SortableHeader label="Stage" sortKey="stage" current={sortKey} asc={sortAsc} onSort={toggleSort} />
                <SortableHeader label="Status" sortKey="status" current={sortKey} asc={sortAsc} onSort={toggleSort} />
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredMappings.map((m, idx) => (
                <React.Fragment key={m.id}>
                  <tr
                    data-row-cursor={idx === cursor ? 'true' : undefined}
                    onClick={() => setCursor(idx)}
                    className={`hover:bg-gray-50 transition-colors ${
                      idx === cursor ? 'ring-2 ring-inset ring-primary-400' : ''
                    } ${selected.has(m.id) ? 'bg-primary-50' : ''}`}
                  >
                    <td className="px-3 py-2.5">
                      <input
                        type="checkbox"
                        checked={selected.has(m.id)}
                        onChange={() => toggleSelect(m.id)}
                        className="rounded"
                      />
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs font-medium text-gray-900">
                      {m.raw_column}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-primary-700">
                      {m.curator_field || m.matched_field || (
                        <span className="text-gray-400 italic">unmapped</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      <ConfidenceBadge score={m.confidence_score} size="sm" />
                    </td>
                    <td className="px-3 py-2.5">
                      <StageBadge stage={m.stage} />
                    </td>
                    <td className="px-3 py-2.5">
                      <StatusBadge status={m.status} />
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1">
                        {m.status !== 'accepted' && (
                          <button
                            onClick={() => handleAccept(m.id)}
                            className="p-1 rounded hover:bg-green-100 text-green-600"
                            title="Accept"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        {m.status !== 'rejected' && (
                          <button
                            onClick={() => handleReject(m.id)}
                            className="p-1 rounded hover:bg-red-100 text-red-600"
                            title="Reject"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => openEdit(m)}
                          className="p-1 rounded hover:bg-blue-100 text-blue-600"
                          title="Edit"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setExpandedRow(expandedRow === m.id ? null : m.id)}
                          className="p-1 rounded hover:bg-gray-200 text-gray-500"
                          title="Details"
                        >
                          {expandedRow === m.id ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>

                  {/* Expanded detail */}
                  {expandedRow === m.id && (
                    <tr>
                      <td colSpan={7} className="bg-gray-50 px-6 py-4">
                        <div className="grid grid-cols-2 gap-6 text-xs">
                          <div>
                            <h4 className="font-semibold text-gray-700 mb-2">
                              Top-5 Alternative Matches
                            </h4>
                            {m.alternatives.length > 0 ? (
                              <ul className="space-y-1">
                                {m.alternatives.map((alt, i) => (
                                  <li key={`${alt.field}-${i}`} className="flex items-center gap-2">
                                    <span className="font-mono text-primary-700">
                                      {alt.field}
                                    </span>
                                    <ConfidenceBadge
                                      score={alt.score}
                                      size="sm"
                                    />
                                    <span className="text-gray-400">
                                      {alt.method}
                                    </span>
                                    {m.status !== 'accepted' && (
                                      <button
                                        onClick={() => handleApplyAlternative(m.id, alt.field)}
                                        className="ml-auto rounded-md px-2 py-0.5 text-[11px] font-semibold text-primary-600 hover:bg-primary-50"
                                      >
                                        Apply
                                      </button>
                                    )}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-gray-400 italic">
                                No alternative matches
                              </p>
                            )}

                            {/* On-demand Stage-4 LLM rematch */}
                            <div className="mt-3 border-t border-gray-200 pt-3">
                              <button
                                onClick={() => handleLlmRematch(m.id)}
                                disabled={llmBusyId === m.id}
                                className="flex items-center gap-1.5 rounded-md bg-orange-50 px-2.5 py-1 text-[11px] font-semibold text-orange-700 hover:bg-orange-100 disabled:opacity-60"
                              >
                                <Sparkles className="h-3.5 w-3.5" />
                                {llmBusyId === m.id ? 'Asking the LLM…' : 'Try LLM rematch'}
                              </button>
                              {llmResults[m.id]?.length > 0 && (
                                <ul className="mt-2 space-y-1">
                                  {llmResults[m.id].map((s, i) => (
                                    <li key={`llm-${s.field}-${i}`} className="flex items-center gap-2">
                                      <Sparkles className="h-3 w-3 text-orange-400" />
                                      <span className="font-mono text-orange-700">{s.field}</span>
                                      <ConfidenceBadge score={s.confidence} size="sm" />
                                      {m.status !== 'accepted' && (
                                        <button
                                          onClick={() => handleApplyAlternative(m.id, s.field)}
                                          className="ml-auto rounded-md px-2 py-0.5 text-[11px] font-semibold text-orange-600 hover:bg-orange-50"
                                        >
                                          Apply
                                        </button>
                                      )}
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-700 mb-2">
                              Mapping Details
                            </h4>
                            <dl className="space-y-1">
                              <dt className="text-gray-500">Method</dt>
                              <dd className="text-gray-900">
                                {m.method || 'N/A'}
                              </dd>
                              <dt className="text-gray-500 mt-2">
                                Curator Note
                              </dt>
                              <dd className="text-gray-900">
                                {m.curator_note || '—'}
                              </dd>
                              {m.reviewed_at && (
                                <>
                                  <dt className="text-gray-500 mt-2">
                                    Reviewed
                                  </dt>
                                  <dd className="text-gray-900">
                                    {new Date(m.reviewed_at).toLocaleString()}
                                  </dd>
                                </>
                              )}
                            </dl>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>

          {filteredMappings.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              No mappings match the current filters.
            </div>
          )}
        </div>
      )}

      {/* Edit Modal */}
      {editingId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Edit Mapping</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                New field name
              </label>
              <input
                value={editField}
                onChange={(e) => setEditField(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                placeholder="e.g. sex, age_years, body_site"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Note (optional)
              </label>
              <textarea
                value={editNote}
                onChange={(e) => setEditNote(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                rows={2}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setEditingId(null);
                  setEditField('');
                  setEditNote('');
                }}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleEditSubmit}
                disabled={!editField.trim()}
                className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* Sortable header cell */
function SortableHeader({
  label,
  sortKey,
  current,
  asc,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  current: SortKey;
  asc: boolean;
  onSort: (k: SortKey) => void;
}) {
  return (
    <th
      className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer select-none hover:text-gray-700"
      onClick={() => onSort(sortKey)}
    >
      <span className="flex items-center gap-1">
        {label}
        <ArrowUpDown className="w-3 h-3" />
        {current === sortKey && (
          <span className="text-primary-600">{asc ? '↑' : '↓'}</span>
        )}
      </span>
    </th>
  );
}
