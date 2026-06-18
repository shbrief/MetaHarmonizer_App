import { useParams, useNavigate } from 'react-router-dom';
import { Download, FileText, Database, FileJson, CircleCheck } from 'lucide-react';
import { toast } from 'sonner';
import { getExportUrl } from '../api/client';
import { useDeleteStudy, useStudies } from '../hooks/queries';
import PageHeader from '../components/ui/PageHeader';
import { Card, CardBody } from '../components/ui/Card';
import StudyPicker from '../components/StudyPicker';

export default function ExportPage() {
  const { studyId } = useParams<{ studyId: string }>();
  const navigate = useNavigate();
  const { data: studies, isLoading } = useStudies();
  const del = useDeleteStudy();

  if (!studyId) {
    return (
      <StudyPicker
        title="Export harmonized data"
        description="Pick a study to download its harmonized outputs."
        studies={studies}
        loading={isLoading}
        basePath="/export"
      />
    );
  }

  const study = studies?.find((s) => s.id === studyId);

  const exports = [
    {
      icon: FileText,
      title: 'Harmonized CSV',
      desc: 'Data with columns renamed to curated schema fields and ontology IDs added.',
      format: 'harmonized' as const,
      tone: 'bg-emerald-50 text-emerald-600',
    },
    {
      icon: Database,
      title: 'cBioPortal Format',
      desc: 'Tab-separated file with cBioPortal clinical header lines, ready for the importer.',
      format: 'cbioportal' as const,
      tone: 'bg-primary-50 text-primary-600',
    },
    {
      icon: FileJson,
      title: 'Mapping Report (JSON)',
      desc: 'Full audit trail of mapping decisions, curator edits, and metadata.',
      format: 'report' as const,
      tone: 'bg-purple-50 text-purple-600',
    },
  ];

  const onComplete = () => {
    if (!studyId) return;
    del.mutate(studyId, {
      onSuccess: () => {
        toast.success('Study completed and removed');
        navigate('/export');
      },
      onError: () => toast.error('Could not complete study'),
    });
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Export harmonized data"
      >
        {study && (
          <p className="mt-1 text-sm text-slate-500">
            {study.row_count} rows · {study.column_count} columns
          </p>
        )}
      </PageHeader>

      <div className="grid gap-4">
        {exports.map(({ icon: Icon, title, desc, format, tone }) => (
          <Card key={format} className="transition hover:shadow-card">
            <CardBody className="flex items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className={`grid h-12 w-12 place-items-center rounded-2xl ${tone}`}>
                  <Icon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
                  <p className="mt-1 max-w-md text-xs text-slate-500">{desc}</p>
                </div>
              </div>
              <a href={getExportUrl(studyId, format)} download className="btn-primary btn-sm shrink-0">
                <Download className="h-4 w-4" />
                Download
              </a>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Study lifecycle action — completing removes the study */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
        <p className="text-xs text-slate-500">
          Completing removes this study and its mappings. Studies left incomplete are
          auto-removed after a week.
        </p>
        <button
          onClick={onComplete}
          disabled={del.isPending}
          title="Mark complete and remove this study"
          className="group/btn inline-flex shrink-0 items-center gap-2 rounded-full border border-emerald-200 bg-white px-4 py-2 text-sm font-semibold text-emerald-700 shadow-sm transition hover:border-emerald-300 hover:bg-emerald-50 hover:shadow active:scale-95 disabled:opacity-60"
        >
          <CircleCheck className="h-4 w-4 transition group-hover/btn:scale-110" />
          Complete &amp; remove
        </button>
      </div>
    </div>
  );
}
