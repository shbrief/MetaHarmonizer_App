import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Upload,
  Table2,
  Microscope,
  Download,
  Layers,
  Database,
  Columns3,
  Clock,
  Gauge,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  FileSpreadsheet,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { useOverview } from '../hooks/queries';
import { useAuth } from '../context/AuthContext';
import { Card, CardBody } from '../components/ui/Card';
import { EmptyState, LoadingBlock } from '../components/ui/Feedback';
import AnimatedNumber from '../components/ui/AnimatedNumber';
import RadialProgress from '../components/ui/RadialProgress';
import { Stagger, StaggerItem } from '../components/ui/motion';
import Badge from '../components/ui/Badge';
import type { StageBreakdown, StudySummary } from '../api/types';

const STAGE_META: Record<string, { label: string; color: string }> = {
  stage1: { label: 'Dict / Fuzzy', color: '#2547e8' },
  stage2: { label: 'Value / Ontology', color: '#6366f1' },
  stage3: { label: 'Semantic', color: '#a855f7' },
  stage4: { label: 'LLM', color: '#17ad84' },
  invalid: { label: 'Invalid', color: '#f43f5e' },
  unmapped: { label: 'Unmapped', color: '#94a3b8' },
};

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data, isLoading } = useOverview();

  const greeting = getGreeting();
  const firstName = (user?.name || user?.email || '').split(/[\s@]/)[0];

  return (
    <div className="space-y-7">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-primary-700 via-primary-600 to-indigo-700 p-7 text-white shadow-card sm:p-9"
      >
        <div className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 right-24 h-56 w-56 rounded-full bg-accent-400/20 blur-3xl" />
        <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-primary-100">
              {greeting}{firstName ? `, ${firstName}` : ''} 👋
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">
              Harmonization overview
            </h1>
            <p className="mt-2 max-w-md text-sm text-primary-100">
              Track mapping progress across every study and jump straight into the work
              that needs your review.
            </p>
            <div className="mt-5 flex flex-wrap gap-2.5">
              <Link to="/upload" className="btn bg-white text-primary-700 hover:bg-primary-50">
                <Upload className="h-4 w-4" />
                Upload study
              </Link>
              <Link
                to="/review"
                className="btn border border-white/30 bg-white/10 text-white backdrop-blur hover:bg-white/20"
              >
                <Table2 className="h-4 w-4" />
                Review mappings
              </Link>
            </div>
          </div>

          {data && data.total_columns > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.15, duration: 0.4 }}
              className="shrink-0 rounded-2xl bg-white/10 p-4 backdrop-blur"
            >
              <RadialProgress
                value={data.review_progress}
                tone="#ffffff"
                track="rgba(255,255,255,0.25)"
                label="reviewed"
                dark
              />
            </motion.div>
          )}
        </div>
      </motion.div>

      {isLoading ? (
        <LoadingBlock label="Loading your workspace…" />
      ) : !data || data.total_studies === 0 ? (
        <EmptyState
          icon={<Upload className="h-6 w-6" />}
          title="No studies yet"
          description="Upload a clinical metadata file to start harmonizing and this dashboard will come alive."
          action={
            <Link to="/upload" className="btn-primary">
              <Upload className="h-4 w-4" />
              Upload your first study
            </Link>
          }
        />
      ) : (
        <>
          {/* KPI tiles */}
          <Stagger className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatTile
              icon={<Database className="h-5 w-5" />}
              tone="from-primary-500 to-primary-700"
              label="Studies"
              value={data.total_studies}
              hint={`${data.total_rows.toLocaleString()} rows total`}
            />
            <StatTile
              icon={<Columns3 className="h-5 w-5" />}
              tone="from-indigo-500 to-indigo-700"
              label="Columns mapped"
              value={data.mapped_columns}
              hint={`of ${data.total_columns.toLocaleString()} columns`}
            />
            <StatTile
              icon={<Clock className="h-5 w-5" />}
              tone="from-amber-500 to-orange-600"
              label="Pending review"
              value={data.pending_review}
              hint="awaiting a curator"
            />
            <StatTile
              icon={<Gauge className="h-5 w-5" />}
              tone="from-accent-500 to-accent-700"
              label="Avg confidence"
              value={data.avg_confidence * 100}
              decimals={1}
              suffix="%"
              hint="across all matches"
            />
          </Stagger>

          {/* Middle row: progress + stage breakdown */}
          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardBody className="flex flex-col items-center justify-center gap-4 py-8">
                <RadialProgress value={data.review_progress} label="reviewed" size={150} />
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-800">Review progress</p>
                  <p className="mt-1 text-xs text-slate-500">
                    <AnimatedNumber value={data.accepted} /> accepted ·{' '}
                    <AnimatedNumber value={data.rejected} /> rejected
                  </p>
                </div>
              </CardBody>
            </Card>

            <Card className="lg:col-span-2">
              <CardBody>
                <div className="mb-5 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-slate-400" />
                    <h3 className="text-sm font-semibold text-slate-800">Stage breakdown</h3>
                  </div>
                  <span className="text-xs text-slate-400">
                    {data.total_columns.toLocaleString()} columns
                  </span>
                </div>
                <StageBars stages={data.stage_breakdown} total={data.total_columns} />
              </CardBody>
            </Card>
          </div>

          {/* Recent studies */}
          <Card>
            <CardBody>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-800">Your studies</h3>
                <Link
                  to="/review"
                  className="flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-700"
                >
                  Review all
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
              <Stagger className="grid gap-3 sm:grid-cols-2">
                {data.studies.slice(0, 6).map((s) => (
                  <StaggerItem key={s.id}>
                    <StudyRow study={s} onClick={() => navigate(`/review/${s.id}`)} />
                  </StaggerItem>
                ))}
              </Stagger>
            </CardBody>
          </Card>

          {/* Quick actions */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <QuickAction to="/upload" icon={<Upload className="h-5 w-5" />} title="Upload" desc="Harmonize a new study" tone="bg-primary-50 text-primary-600" />
            <QuickAction to="/review" icon={<Table2 className="h-5 w-5" />} title="Mapping review" desc="Curate column mappings" tone="bg-indigo-50 text-indigo-600" />
            <QuickAction to="/ontology" icon={<Microscope className="h-5 w-5" />} title="Ontology" desc="Map values to terms" tone="bg-purple-50 text-purple-600" />
            <QuickAction to="/export" icon={<Download className="h-5 w-5" />} title="Export" desc="Download results" tone="bg-accent-100 text-accent-700" />
          </div>
        </>
      )}
    </div>
  );
}

/* ---------- pieces ---------- */

function StatTile({
  icon,
  tone,
  label,
  value,
  hint,
  decimals = 0,
  suffix = '',
}: {
  icon: ReactNode;
  tone: string;
  label: string;
  value: number;
  hint?: string;
  decimals?: number;
  suffix?: string;
}) {
  return (
    <StaggerItem>
      <div className="stat-tile">
        <div className={`mb-3 grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br ${tone} text-white shadow-sm`}>
          {icon}
        </div>
        <div className="text-2xl font-bold tracking-tight text-slate-900">
          <AnimatedNumber value={value} decimals={decimals} suffix={suffix} />
        </div>
        <div className="mt-0.5 text-sm font-medium text-slate-600">{label}</div>
        {hint && <div className="mt-0.5 text-xs text-slate-400">{hint}</div>}
      </div>
    </StaggerItem>
  );
}

function StageBars({ stages, total }: { stages: StageBreakdown[]; total: number }) {
  if (!stages.length) {
    return <p className="py-6 text-center text-sm text-slate-400">No stage data yet.</p>;
  }
  const max = Math.max(...stages.map((s) => s.count), 1);
  return (
    <div className="space-y-3">
      {stages.map((s, i) => {
        const meta = STAGE_META[s.stage] ?? { label: s.stage, color: '#94a3b8' };
        const pct = (s.count / max) * 100;
        return (
          <div key={s.stage} className="flex items-center gap-3">
            <div className="w-28 shrink-0 text-xs font-medium text-slate-600">{meta.label}</div>
            <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: meta.color }}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.7, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
            <div className="w-20 shrink-0 text-right text-xs text-slate-500">
              {s.count} · {total ? Math.round((s.count / total) * 100) : 0}%
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StudyRow({ study, onClick }: { study: StudySummary; onClick: () => void }) {
  const pct = Math.round(study.review_progress * 100);
  const done = pct >= 100;
  return (
    <button onClick={onClick} className="group w-full text-left">
      <div className="card-hover flex items-center gap-3 p-4">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary-50 text-primary-600">
          <FileSpreadsheet className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold text-slate-900">{study.name}</p>
            {done ? (
              <Badge tone="green">
                <CheckCircle2 className="h-3 w-3" />
                Done
              </Badge>
            ) : study.pending_review > 0 ? (
              <Badge tone="amber">{study.pending_review} pending</Badge>
            ) : null}
          </div>
          <div className="mt-1.5 flex items-center gap-2">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-primary-500" style={{ width: `${pct}%` }} />
            </div>
            <span className="w-10 text-right text-[11px] font-medium text-slate-500">{pct}%</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            {study.column_count ?? '—'} columns · {study.mapped_columns} mapped
          </p>
        </div>
        <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-primary-500" />
      </div>
    </button>
  );
}

function QuickAction({
  to,
  icon,
  title,
  desc,
  tone,
}: {
  to: string;
  icon: ReactNode;
  title: string;
  desc: string;
  tone: string;
}) {
  return (
    <Link to={to} className="group">
      <div className="card-hover flex items-center gap-3 p-4">
        <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${tone}`}>{icon}</span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="truncate text-xs text-slate-500">{desc}</p>
        </div>
        <Sparkles className="ml-auto h-4 w-4 text-slate-200 transition group-hover:text-primary-400" />
      </div>
    </Link>
  );
}

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}
