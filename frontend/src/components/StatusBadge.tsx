
interface Props {
  status: string;
}

const STATUS_STYLES: Record<string, { label: string; color: string }> = {
  // Familiar green/red for accepted/rejected; icons add a non-colour cue.
  accepted: { label: '✓ Accepted', color: 'text-green-700' },
  rejected: { label: '✗ Rejected', color: 'text-red-700' },
  pending: { label: '⏳ Pending', color: 'text-amber-700' },
};

export default function StatusBadge({ status }: Props) {
  const info = STATUS_STYLES[status] ?? { label: status, color: 'text-gray-500' };
  return <span className={`text-xs font-semibold ${info.color}`}>{info.label}</span>;
}
