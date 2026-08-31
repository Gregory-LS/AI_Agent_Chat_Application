import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'danger' | 'warning' | 'info';
}

const variantStyles = {
  danger: { icon: 'text-red-500', button: 'bg-red-500 hover:bg-red-600' },
  warning: { icon: 'text-yellow-500', button: 'bg-yellow-500 hover:bg-yellow-600' },
  info: { icon: 'text-blue-500', button: 'bg-blue-500 hover:bg-blue-600' },
};

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'danger',
}: ConfirmDialogProps) {
  const [isClosing, setIsClosing] = useState(false);

  if (!isOpen) return null;

  const handleCancel = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      onCancel();
    }, 200);
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 transition-opacity ${
        isClosing ? 'opacity-0' : 'opacity-100'
      }`}
      onClick={handleCancel}
    >
      <div
        className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className={`w-6 h-6 ${variantStyles[variant].icon}`} />
          <h2 className="text-lg font-semibold">{title}</h2>
        </div>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={handleCancel}
            className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={() => {
              onConfirm();
            }}
            className={`px-4 py-2 rounded text-white transition-colors ${variantStyles[variant].button}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
