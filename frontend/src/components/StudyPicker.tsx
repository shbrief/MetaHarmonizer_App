import { useNavigate } from 'react-router-dom';
import { FileSpreadsheet, ArrowRight, Upload } from 'lucide-react';
import type { Study } from '../api/types';
import { Card } from './ui/Card';
import Button from './ui/Button';
import Badge from './ui/Badge';
import { EmptyState, LoadingBlock } from './ui/Feedback';
import PageHeader from './ui/PageHeader';

/** Landing list shown by review/quality/export pages when no study is selected. */
export default function StudyPicker({
  title,
  description,
  studies,
  loading,
  basePath,
}: {
  title: string;
  description?: string;
  studies: Study[] | undefined;
  loading: boolean;
  /** e.g. '/review' — navigates to `${basePath}/${study.id}`. */
  basePath: string;
}) {
  const navigate = useNavigate();

  return (
    <div>
      <PageHeader title={title} description={description} />
      {loading ? (
        <LoadingBlock label="Loading studies…" />
      ) : !studies?.length ? (
        <EmptyState
          icon={<Upload className="h-6 w-6" />}
          title="No studies yet"
          description="Upload a metadata file to start harmonizing."
          action={
            <Button icon={<Upload className="h-4 w-4" />} onClick={() => navigate('/')}>
              Upload a file
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {studies.map((s) => (
            <button
              key={s.id}
              onClick={() => navigate(`${basePath}/${s.id}`)}
              className="group text-left"
            >
              <Card className="flex items-center justify-between gap-3 p-4 transition hover:border-primary-300 hover:shadow-card">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary-50 text-primary-600">
                    <FileSpreadsheet className="h-5 w-5" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-slate-900">{s.name}</p>
                    <p className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                      <span>{s.row_count ?? '—'} rows</span>·
                      <span>{s.column_count ?? '—'} columns</span>
                      {s.status && <Badge tone="slate">{s.status}</Badge>}
                    </p>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-primary-500" />
              </Card>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Compact study switcher used in page headers. */
export function StudySelect({
  studies,
  value,
  onChange,
}: {
  studies: Study[] | undefined;
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="field !w-auto !py-2">
      {studies?.map((s) => (
        <option key={s.id} value={s.id}>
          {s.name}
        </option>
      ))}
    </select>
  );
}
