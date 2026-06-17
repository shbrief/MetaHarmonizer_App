import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, AlertCircle, FileSpreadsheet, ArrowRight, Sparkles, Loader2, X } from 'lucide-react';
import { toast } from 'sonner';
import FileUploader from '../components/FileUploader';
import PageHeader from '../components/ui/PageHeader';
import { Card, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { uploadAndHarmonize } from '../api/client';
import { subscribeJob, type JobSubscription } from '../api/jobs';
import { ApiError } from '../api/http';
import type { HarmonizeAccepted, JobProgress } from '../api/types';

type UploadState = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

const STAGES = [
  { stage: 'Stage 1', title: 'Dict / Fuzzy', desc: 'Dictionary lookup + RapidFuzz string matching against curated fields', tone: 'bg-primary-50 text-primary-700' },
  { stage: 'Stage 2', title: 'Value / Ontology', desc: 'Column value overlap analysis using ontology-aware matching', tone: 'bg-indigo-50 text-indigo-700' },
  { stage: 'Stage 3', title: 'Semantic', desc: 'Sentence-transformer embeddings (all-MiniLM-L6-v2) cosine similarity', tone: 'bg-purple-50 text-purple-700' },
  { stage: 'Stage 4', title: 'LLM', desc: 'Large-language-model fallback for columns unmatched by earlier stages', tone: 'bg-accent-100 text-accent-700' },
];

export default function UploadPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [state, setState] = useState<UploadState>('idle');
  const [accepted, setAccepted] = useState<HarmonizeAccepted | null>(null);
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const subRef = useRef<JobSubscription | null>(null);

  const handleFileSelected = (f: File) => {
    setFile(f);
    setError(null);
    setState('idle');
    setProgress(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setState('uploading');
    setError(null);
    setProgress(null);
    try {
      const res = await uploadAndHarmonize(file);
      setAccepted(res);
      setState('processing');
      qc.invalidateQueries({ queryKey: ['studies'] });

      // Open the live progress stream.
      subRef.current = await subscribeJob(res.study_id, {
        onProgress: (p) => {
          setProgress(p);
          if (p.type === 'complete') {
            setState('success');
            qc.invalidateQueries({ queryKey: ['studies'] });
            qc.invalidateQueries({ queryKey: ['overview'] });
            toast.success('Harmonization complete');
            subRef.current?.close();
          } else if (p.type === 'failed') {
            setState('error');
            setError(p.message);
            toast.error(p.message);
            subRef.current?.close();
          } else if (p.type === 'cancelled') {
            setState('idle');
            setProgress(null);
            toast('Harmonization cancelled');
            subRef.current?.close();
          }
        },
        onError: () => {
          // WS dropped — fall back to a gentle message; the job still runs.
          toast('Live updates interrupted — refresh to check status.');
        },
      });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Upload failed';
      setError(msg);
      setState('error');
      toast.error(msg);
    }
  };

  const handleCancel = () => {
    subRef.current?.cancel();
    toast('Cancelling…');
  };

  return (
    <div className="mx-auto max-w-3xl space-y-7">
      <PageHeader
        title="Upload study metadata"
        description="Upload a CSV/TSV file with clinical metadata. The pipeline maps columns to the curated reference schema automatically."
      />

      <FileUploader onFileSelected={handleFileSelected} disabled={state === 'uploading' || state === 'processing'} />

      {/* Selected file → run */}
      {file && state !== 'success' && state !== 'processing' && (
        <Card>
          <CardBody className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary-50 text-primary-600">
                <FileSpreadsheet className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-900">{file.name}</p>
                <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <Button
              onClick={handleUpload}
              loading={state === 'uploading'}
              icon={state === 'uploading' ? undefined : <Sparkles className="h-4 w-4" />}
            >
              {state === 'uploading' ? 'Uploading…' : 'Run harmonization'}
            </Button>
          </CardBody>
        </Card>
      )}

      {/* Live processing */}
      {state === 'processing' && accepted && (
        <Card className="border-primary-200">
          <CardBody className="space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <Loader2 className="mt-0.5 h-6 w-6 animate-spin text-primary-600" />
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Harmonizing {accepted.study_name}…</h3>
                  <p className="mt-0.5 text-sm text-slate-500">
                    {progress?.message ?? 'Starting…'} · {accepted.row_count.toLocaleString()} rows ·{' '}
                    {accepted.column_count} columns
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" className="text-rose-600 hover:bg-rose-50" icon={<X className="h-3.5 w-3.5" />} onClick={handleCancel}>
                Cancel
              </Button>
            </div>

            {/* Progress bar */}
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-primary-500 transition-all duration-500"
                style={{ width: `${progress?.pct ?? 5}%` }}
              />
            </div>

            {/* Stage pills */}
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'parse', label: 'Read file' },
                { key: 'schema', label: 'Schema mapping' },
                { key: 'ontology', label: 'Ontology' },
                { key: 'done', label: 'Finalize' },
              ].map((s) => {
                const reached = (progress?.pct ?? 0) >= stagePct(s.key);
                const active = progress?.stage === s.key;
                return (
                  <span
                    key={s.key}
                    className={`chip ${active ? 'bg-primary-600 text-white' : reached ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}
                  >
                    {reached && !active ? <CheckCircle2 className="h-3 w-3" /> : null}
                    {s.label}
                  </span>
                );
              })}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Success */}
      {state === 'success' && accepted && (
        <Card className="border-emerald-200 bg-emerald-50/40">
          <CardBody className="space-y-5">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-6 w-6 text-emerald-600" />
              <div>
                <h3 className="text-lg font-semibold text-emerald-900">Harmonization complete</h3>
                <p className="mt-0.5 text-sm text-emerald-700">{progress?.message ?? 'Done.'}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Stat label="Study" value={accepted.study_name} />
              <Stat label="Rows" value={accepted.row_count.toLocaleString()} />
              <Stat label="Columns" value={accepted.column_count.toLocaleString()} />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={() => navigate(`/review/${accepted.study_id}`)} icon={<ArrowRight className="h-4 w-4" />}>
                Review mappings
              </Button>
              <Button variant="secondary" onClick={() => navigate(`/quality/${accepted.study_id}`)}>
                View quality dashboard
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Error */}
      {state === 'error' && error && (
        <Card className="border-rose-200 bg-rose-50/50">
          <CardBody className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 text-rose-600" />
            <div>
              <h3 className="text-sm font-semibold text-rose-900">Harmonization failed</h3>
              <p className="mt-0.5 text-sm text-rose-700">{error}</p>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Pipeline explainer */}
      <Card>
        <CardBody>
          <h3 className="text-sm font-semibold text-slate-900">How the pipeline works</h3>
          <p className="mb-5 mt-1 text-xs text-slate-500">
            Powered by the MetaHarmonizer SchemaMapEngine — a 4-stage cascade.
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {STAGES.map((s) => (
              <div key={s.stage} className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
                <span className={`chip ${s.tone}`}>{s.stage}</span>
                <p className="mt-2 text-sm font-semibold text-slate-900">{s.title}</p>
                <p className="mt-1 text-xs text-slate-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-emerald-200 bg-white p-3 text-center">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-0.5 truncate text-lg font-bold text-slate-900" title={value}>
        {value}
      </div>
    </div>
  );
}

/** Progress threshold (%) at which a stage is considered reached. */
function stagePct(key: string): number {
  switch (key) {
    case 'parse': return 10;
    case 'schema': return 30;
    case 'ontology': return 90;
    case 'done': return 100;
    default: return 100;
  }
}
