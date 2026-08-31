import { RotateCcw } from 'lucide-react';

interface RegenerateButtonProps {
  onClick: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export default function RegenerateButton({ onClick, isLoading = false, disabled = false }: RegenerateButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors ${
        isLoading
          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
          : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
      }`}
    >
      <RotateCcw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
      {isLoading ? 'Regenerating...' : 'Regenerate'}
    </button>
  );
}
