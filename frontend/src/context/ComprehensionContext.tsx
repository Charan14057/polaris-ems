import React, { createContext, useContext, useState } from 'react';

export type ComprehensionMode = 'simple' | 'technical';

interface ComprehensionContextValue {
  mode: ComprehensionMode;
  setMode: (mode: ComprehensionMode) => void;
  toggleMode: () => void;
  isOrientationOpen: boolean;
  openOrientation: () => void;
  closeOrientation: () => void;
}

const ComprehensionContext = createContext<ComprehensionContextValue | undefined>(undefined);

export const ComprehensionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<ComprehensionMode>('simple');
  const [isOrientationOpen, setIsOrientationOpen] = useState(false);

  const toggleMode = () => {
    setMode((prev) => (prev === 'simple' ? 'technical' : 'simple'));
  };

  return (
    <ComprehensionContext.Provider
      value={{
        mode,
        setMode,
        toggleMode,
        isOrientationOpen,
        openOrientation: () => setIsOrientationOpen(true),
        closeOrientation: () => setIsOrientationOpen(false),
      }}
    >
      {children}
    </ComprehensionContext.Provider>
  );
};

export const useComprehension = (): ComprehensionContextValue => {
  const context = useContext(ComprehensionContext);
  if (!context) {
    throw new Error('useComprehension must be used within a ComprehensionProvider');
  }
  return context;
};
