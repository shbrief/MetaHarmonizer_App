import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, AlertCircle, FileSpreadsheet, ArrowRight, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import FileUploader from '../components/FileUploader';
import PageHeader from '../components/ui/PageHeader';
import { Card, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { uploadAndHarmonize } from '../api/client';
import { ApiError } from '../api/http';
import type { HarmonizeResponse } from '../api/types';

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

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
  const [result, setResult] = useState<HarmonizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const handleFileSelected = (f: File) => {
    setFile(f);
    setError(null);
    setState('idle');
  };

  const handleUpload = async () => {
    if (!file) return;
    setState('uploading');
    setError(null);
    try {
      const res = await uploadAndHarmonize(file);
      setResult(res);
      setState('success');
      qc.invalidateQueries({ queryKey: ['studies'] });
      toast.success('Harmonization complete');
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Upload failed';
      setError(msg);
      setState('error');
      toast.error(msg);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-7">
      <PageHeader
        title="Upload study metadata"
        description="Upload a CSV/TSV file with clinical metadata. The pipeline maps columns to the curated reference schema automatically."
      />

      <FileUploader onFileSelected={handleFileSelected} disabled={state === 'uploading'} />

      {/* Selected file → run */}
      {file && state !== 'success' && (
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
              {state === 'uploading' ? 'Harmonizing…' : 'Run harmonization'}
            </Button>
          </CardBody>
        </Card>
      )}

      {/* Success */}
      {state === 'success' && result && (
        <Card className="border-emerald-200 bg-emerald-50/40">
          <CardBody className="space-y-5">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-6 w-6 text-emerald-600" />
              <div>
                <h3 className="text-lg font-semibold text-emerald-900">Harmonization complete</h3>
                <p className="mt-0.5 text-sm text-emerald-700">{result.message}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Stat label="Study" value={result.study_name} />
              <Stat label="Rows" value={result.row_count.toLocaleString()} />
              <Stat label="Columns" value={result.column_count.toLocaleString()} />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={() => navigate(`/review/${result.job_id}`)} icon={<ArrowRight className="h-4 w-4" />}>
                Review mappings
              </Button>
              <Button variant="secondary" onClick={() => navigate(`/quality/${result.job_id}`)}>
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
              <h3 className="text-sm font-semibold text-rose-900">Upload failed</h3>
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
