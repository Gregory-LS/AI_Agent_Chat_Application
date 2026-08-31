import { ReactNode } from 'react';

interface TransitionWrapperProps {
  children: ReactNode;
  show: boolean;
  type?: 'fade' | 'slide-up' | 'scale';
  className?: string;
}

const transitionClasses = {
  'fade': 'transition-opacity duration-300',
  'slide-up': 'transition-all duration-300 transform',
  'scale': 'transition-all duration-300 transform',
};

export default function TransitionWrapper({ children, show, type = 'fade', className = '' }: TransitionWrapperProps) {
  const base = transitionClasses[type];
  let stateClasses = '';
  if (type === 'fade') {
    stateClasses = show ? 'opacity-100' : 'opacity-0';
  } else if (type === 'slide-up') {
    stateClasses = show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4';
  } else if (type === 'scale') {
    stateClasses = show ? 'opacity-100 scale-100' : 'opacity-0 scale-95';
  }

  if (!show) return null;

  return (
    <div className={`${base} ${stateClasses} ${className}`}>
      {children}
    </div>
  );
}
