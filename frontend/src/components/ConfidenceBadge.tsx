
interface Props {
  score: number | null;
  size?: 'sm' | 'md';
}

/**
 * Colour-coded confidence badge (green→amber→red ramp; the High/Med/Low label
 * is a redundant non-colour cue):
 *  >=0.9 green (high), 0.5-0.9 amber (review), <0.5 red (low)
 */
export default function ConfidenceBadge({ score, size = 'md' }: Props) {
  if (score === null || score === undefined) {
    return <span className="text-gray-400 text-xs">—</span>;
  }

  let bg: string;
  let text: string;
  if (score >= 0.9) {
    bg = 'bg-green-100 text-green-800';
    text = 'High';
  } else if (score >= 0.5) {
    bg = 'bg-amber-100 text-amber-800';
    text = 'Med';
  } else {
    bg = 'bg-red-100 text-red-800';
    text = 'Low';
  }

  const sizeClass = size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-full ${bg} ${sizeClass}`}
      title={`Confidence: ${(score * 100).toFixed(1)}%`}
    >
      {(score * 100).toFixed(0)}%
      <span className="text-[10px] opacity-70">{text}</span>
    </span>
  );
}
