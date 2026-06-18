import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { FileSpreadsheet, ArrowRight, CircleCheck, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import type { Study } from '../api/types';
import { Card } from './ui/Card';
import Badge from './ui/Badge';
import { useDeleteStudy } from '../hooks/queries';

const CONFETTI = ['#22c55e', '#16a34a', '#86efac', '#4ade80', '#bbf7d0', '#34d399'];

/** A green burst of particles flying outward from the card centre. */
function Confetti() {
  return (
    <>
      {Array.from({ length: 18 }).map((_, i) => {
        const angle = (i / 18) * Math.PI * 2;
        const dist = 55 + Math.random() * 40;
        return (
          <motion.span
            key={i}
            className="absolute left-1/2 top-1/2 h-2 w-2 rounded-[2px]"
            style={{ backgroundColor: CONFETTI[i % CONFETTI.length] }}
            initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
            animate={{
              x: Math.cos(angle) * dist,
              y: Math.sin(angle) * dist,
              opacity: 0,
              scale: 0.3,
              rotate: Math.random() * 360,
            }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        );
      })}
    </>
  );
}

/** Study card used in the picker list, with a celebratory delete + a
 *  Checking "Complete" turns the card green, pops a confetti burst, then the
 *  card vanishes as the study is removed. Studies left incomplete are
 *  auto-removed after a week. */
export default function StudyListCard({ study, basePath }: { study: Study; basePath: string }) {
  const navigate = useNavigate();
  const del = useDeleteStudy();
  const [celebrating, setCelebrating] = useState(false);

  const onComplete = () => {
    if (celebrating) return;
    setCelebrating(true);
    // Let the celebration play, then remove the study (the exit animates).
    window.setTimeout(() => {
      del.mutate(study.id, {
        onError: () => {
          setCelebrating(false);
          toast.error('Could not complete study');
        },
      });
    }, 850);
  };

  return (
    <motion.div
      layout
      exit={{ opacity: 0, scale: 0.6, transition: { duration: 0.35, ease: 'easeIn' } }}
    >
      <Card className="relative overflow-hidden transition hover:border-primary-300 hover:shadow-card">
        <AnimatePresence>
          {celebrating && (
            <motion.div
              className="absolute inset-0 z-10 grid place-items-center bg-emerald-500"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <Confetti />
              <motion.div
                initial={{ scale: 0, rotate: -30 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 320, damping: 14 }}
                className="flex flex-col items-center gap-1 text-white"
              >
                <CheckCircle2 className="h-10 w-10" />
                <span className="text-sm font-semibold">Done!</span>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main clickable area */}
        <button
          onClick={() => navigate(`${basePath}/${study.id}`)}
          className="group flex w-full items-center justify-between gap-3 p-4 text-left"
        >
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary-50 text-primary-600">
              <FileSpreadsheet className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <p className="truncate font-semibold text-slate-900">{study.name}</p>
              <p className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <span>{study.row_count ?? '—'} rows</span>·
                <span>{study.column_count ?? '—'} columns</span>
                {study.status && <Badge tone="slate">{study.status}</Badge>}
              </p>
              {study.upload_date && (
                <p className="mt-0.5 text-[11px] text-slate-400">Uploaded {timeAgo(study.upload_date)}</p>
              )}
            </div>
          </div>
          <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-primary-500" />
        </button>

        {/* Action footer — completing removes the study (auto-removed after a
            week otherwise). */}
        <div className="flex items-center justify-between gap-3 border-t border-slate-100 bg-slate-50/60 px-4 py-2.5">
          <p className="text-[11px] leading-tight text-slate-400">
            Completing removes this study.
            <br className="hidden sm:block" />
            Left alone, it auto-deletes in a week.
          </p>
          <button
            type="button"
            onClick={onComplete}
            disabled={celebrating}
            title="Mark complete and remove this study"
            className="group/btn inline-flex shrink-0 items-center gap-1.5 rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-xs font-semibold text-emerald-700 shadow-sm transition hover:border-emerald-300 hover:bg-emerald-50 hover:shadow active:scale-95 disabled:opacity-60"
          >
            <CircleCheck className="h-4 w-4 transition group-hover/btn:scale-110" />
            Complete
          </button>
        </div>
      </Card>
    </motion.div>
  );
}

/** Human-friendly relative time, e.g. "just now", "3m ago", "2h ago", "5d ago". */
function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(diff)) return '';
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}
