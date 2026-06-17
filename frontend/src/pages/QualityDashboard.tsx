import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { getQualityMetrics } from '../api/client';
import { useStudies } from '../hooks/queries';
import PageHeader from '../components/ui/PageHeader';
import { Card, CardBody } from '../components/ui/Card';
import { LoadingBlock } from '../components/ui/Feedback';
import StudyPicker, { StudySelect } from '../components/StudyPicker';

const STAGE_COLORS: Record<string, string> = {
  stage1: '#3b66f5',
  stage2: '#6366f1',
  stage3: '#a855f7',
  stage4: '#17ad84',
  unmapped: '#94a3b8',
};

const STATUS_COLORS = ['#22c55e', '#eab308', '#ef4444', '#94a3b8'];

export default function QualityDashboard() {
  const { studyId } = useParams<{ studyId: string }>();
  const navigate = useNavigate();
  const { data: studies, isLoading: studiesLoading } = useStudies();

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['quality', studyId],
    queryFn: () => getQualityMetrics(studyId!),
    enabled: !!studyId,
  });

  if (!studyId) {
    return (
      <StudyPicker
        title="Quality dashboard"
        description="Pick a study to view harmonization quality metrics."
        studies={studies}
        loading={studiesLoading}
        basePath="/quality"
      />
    );
  }

  if (isLoading || !metrics) {
    return <LoadingBlock label="Crunching metrics…" />;
  }

  const statusData = [
    { name: 'Accepted', value: metrics.auto_accepted },
    { name: 'Pending', value: metrics.pending_review },
    { name: 'Rejected', value: metrics.rejected },
    { name: 'New Field', value: metrics.new_field_suggestions },
  ];

  const pipelineCoverage =
    metrics.total_columns > 0
      ? ((metrics.mapped_columns / metrics.total_columns) * 100).toFixed(1)
      : '0';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quality dashboard"
        actions={
          <StudySelect
            studies={studies}
            value={studyId}
            onChange={(id) => navigate(`/quality/${id}`, { replace: true })}
          />
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <KpiCard label="Total Columns" value={metrics.total_columns} />
        <KpiCard label="Mapped" value={metrics.mapped_columns} sub={`${pipelineCoverage}%`} color="text-emerald-600" />
        <KpiCard label="Unmapped" value={metrics.unmapped_columns} color="text-rose-600" />
        <KpiCard label="Avg Confidence" value={`${(metrics.avg_confidence * 100).toFixed(1)}%`} />
        <KpiCard label="Pending Review" value={metrics.pending_review} color="text-amber-600" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Confidence Distribution */}
        <Card>
          <CardBody>
            <h3 className="mb-4 text-sm font-semibold text-slate-700">Confidence Score Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={metrics.confidence_distribution}>
                <XAxis dataKey="bucket" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b66f5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Stage Funnel */}
        <Card>
          <CardBody>
            <h3 className="mb-4 text-sm font-semibold text-slate-700">Stage Breakdown</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={metrics.stage_breakdown} layout="vertical">
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                <YAxis dataKey="stage" type="category" tick={{ fontSize: 12 }} width={80} />
                <Tooltip
                  formatter={(v: number, _: string, props: any) => [
                    `${v} (${props.payload.percentage}%)`,
                    'Columns',
                  ]}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {metrics.stage_breakdown.map((entry) => (
                    <Cell key={entry.stage} fill={STAGE_COLORS[entry.stage] ?? '#94a3b8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Status Pie */}
        <Card>
          <CardBody>
            <h3 className="mb-4 text-sm font-semibold text-slate-700">Review Status</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusData.map((_, i) => (
                    <Cell key={i} fill={STATUS_COLORS[i]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Progress */}
        <Card>
          <CardBody>
            <h3 className="mb-4 text-sm font-semibold text-slate-700">Harmonization Progress</h3>
            <div className="mt-6 space-y-4">
              <ProgressBar label="Mapped" value={metrics.mapped_columns} max={metrics.total_columns} color="bg-emerald-500" />
              <ProgressBar label="Reviewed" value={metrics.auto_accepted + metrics.rejected} max={metrics.total_columns} color="bg-primary-500" />
              <ProgressBar label="Pending" value={metrics.pending_review} max={metrics.total_columns} color="bg-amber-500" />
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <Card className="p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${color ?? 'text-slate-900'}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-400">{sub}</div>}
    </Card>
  );
}

function ProgressBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-slate-600">
        <span>{label}</span>
        <span>
          {value}/{max} ({pct.toFixed(0)}%)
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
