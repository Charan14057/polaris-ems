import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ProvenanceTier } from '../api/types';

export interface EvidenceRecord {
  title?: string;
  value: string | number;
  unit?: string;
  source: string;
  provenance: ProvenanceTier | string;
  timestamp?: string;
  station?: string;
  model?: string;
  modelOrSubsystem?: string;
  uncertainty?: string;
  uncertaintyInterval?: string;
  validationState?: string;
  mathematicalBasis?: string;
  governingInvariant?: string;
  decisionImpact?: string;
}

interface EvidenceContextType {
  activeEvidence: EvidenceRecord | null;
  isOpen: boolean;
  inspectEvidence: (record: EvidenceRecord) => void;
  closeEvidence: () => void;
}

const EvidenceContext = createContext<EvidenceContextType | undefined>(undefined);

export const EvidenceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activeEvidence, setActiveEvidence] = useState<EvidenceRecord | null>(null);
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const inspectEvidence = (record: EvidenceRecord) => {
    setActiveEvidence(record);
    setIsOpen(true);
  };

  const closeEvidence = () => {
    setIsOpen(false);
  };

  return (
    <EvidenceContext.Provider value={{ activeEvidence, isOpen, inspectEvidence, closeEvidence }}>
      {children}
    </EvidenceContext.Provider>
  );
};

const defaultEvidenceContext: EvidenceContextType = {
  activeEvidence: null,
  isOpen: false,
  inspectEvidence: () => {},
  closeEvidence: () => {},
};

export const useEvidence = (): EvidenceContextType => {
  const context = useContext(EvidenceContext);
  return context || defaultEvidenceContext;
};
