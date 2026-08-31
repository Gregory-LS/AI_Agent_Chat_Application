import { Square } from 'lucide-react';

interface StopButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export default function StopButton({ onClick, disabled = false }: StopButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors ${
        disabled
          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
          : 'bg-red-50 text-red-600 hover:bg-red-100'
      }`}
    >
      <Square className="w-4 h-4" />
      Stop
    </button>
  );
}
