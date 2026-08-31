import { FileQuestion } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({
  title = 'No data yet',
  description = 'Your content will appear here.',
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <FileQuestion className="w-16 h-16 text-gray-300 mb-4" />
      <h2 className="text-xl font-semibold text-gray-600">{title}</h2>
      <p className="text-gray-400 mt-2 max-w-md">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
