// JARVIS App — Status Badge
// Used for order status, user status, etc.
// Color mapping is exhaustive — AI adds new statuses here.

type Status =
  | 'active' | 'inactive' | 'pending_approval'
  | 'submitted' | 'opened' | 'in_progress' | 'closed' | 'cancelled'
  | 'draft' | 'published' | string;

const STATUS_STYLES: Record<string, string> = {
  active:           'bg-green-100 text-green-800',
  published:        'bg-green-100 text-green-800',
  closed:           'bg-green-100 text-green-800',
  inactive:         'bg-gray-100 text-gray-600',
  cancelled:        'bg-red-100 text-red-700',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  submitted:        'bg-gray-100 text-gray-700',
  opened:           'bg-blue-100 text-blue-800',
  in_progress:      'bg-yellow-100 text-yellow-800',
  draft:            'bg-gray-100 text-gray-600',
};

const STATUS_LABELS: Record<string, string> = {
  pending_approval: 'Pending Approval',
  in_progress:      'In Progress',
};

interface Props {
  status: Status;
  className?: string;
}

export default function StatusBadge({ status, className = '' }: Props) {
  const style = STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-700';
  const label = STATUS_LABELS[status] ?? status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style} ${className}`}>
      {label}
    </span>
  );
}
