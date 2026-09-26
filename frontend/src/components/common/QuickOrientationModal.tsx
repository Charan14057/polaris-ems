import React, { useState } from 'react';
import { 
  X, 
  ChevronRight, 
  ChevronLeft, 
  Compass, 
  ShieldCheck, 
  Wind, 
  BrainCircuit, 
  Boxes, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2,
  Sparkles
} from 'lucide-react';

interface QuickOrientationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface StepContent {
  title: string;
  badge: string;
  question: string;
  plainAnswer: string;
  howItWorks: string;
  keyTakeaway: string;
  icon: React.ReactNode;
}

export const QuickOrientationModal: React.FC<QuickOrientationModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps: StepContent[] = [
    {
      title: "1. What Problem Does It Solve?",
      badge: "THE POLAR REALITY",
      question: "Why do polar research stations need an autonomous energy system?",
      plainAnswer: "Antarctic research stations (like India's Bharati and Maitri) operate in complete isolation under -40°C temperatures, blinding blizzards, and months of total winter darkness. If the power or heating goes out, the station becomes uninhabitable in hours.",
      howItWorks: "Stations rely on wind turbines, solar panels, large battery banks, and diesel generators. Managing them by hand 24/7 is exhausting, error-prone, and burns thousands of liters of precious shipped-in fuel.",
      keyTakeaway: "Polaris-EMS prioritizes continuous life-support heating and electricity while minimizing diesel fuel use.",
      icon: <Wind className="w-8 h-8 text-ice" />,
    },
    {
      title: "2. What is Polaris-EMS?",
      badge: "THE SYSTEM",
      question: "What actually is this application?",
      plainAnswer: "Polaris-EMS is an intelligent advisory mission control software designed specifically for polar microgrids. It acts as an automated advisory decision-support system for the station's energy management.",
      howItWorks: "It monitors weather forecasts, measures power consumption, runs physics simulations, and automatically schedules the exact minute each generator or battery should charge or discharge.",
      keyTakeaway: "A sovereign mission control that supports operators in keeping the lights and heaters running reliably in Antarctica.",
      icon: <Compass className="w-8 h-8 text-copper" />,
    },
    {
      title: "3. What Does the AI Do?",
      badge: "THE FORECASTING AI",
      question: "How does Artificial Intelligence help?",
      plainAnswer: "The AI looks at incoming weather models and historical station data to forecast what wind speeds, solar light, and scientific energy demand will look like over the next 48 to 168 hours.",
      howItWorks: "Instead of giving a single guess, it produces an uncertainty envelope (P10 to P90). This tells the station operators the worst-case, average, and best-case conditions.",
      keyTakeaway: "Prevents sudden surprises by detecting blizzard wind cut-outs or solar lulls hours before they occur.",
      icon: <BrainCircuit className="w-8 h-8 text-copper" />,
    },
    {
      title: "4. What Does the Digital Twin Do?",
      badge: "THE DIGITAL TWIN",
      question: "What is a 'Digital Twin' in plain English?",
      plainAnswer: "A Digital Twin is a complete virtual replica of the physical station inside the computer. Before changing any real equipment, Polaris-EMS tests the decision inside this simulation first.",
      howItWorks: "It calculates the physical thermodynamics of the building rooms, battery chemistry wear, and electrical grid cables to prove the plan won't overload circuits or freeze pipes.",
      keyTakeaway: "Zero risk to real hardware: every plan is simulated and stress-tested before actuation.",
      icon: <Boxes className="w-8 h-8 text-teal" />,
    },
    {
      title: "5. What Does the Optimizer Do?",
      badge: "THE MATHEMATICAL SOLVER",
      question: "How does the system decide what to turn on or off?",
      plainAnswer: "The optimizer is a mathematical engine (MILP) that solves a massive puzzle every hour: 'What is the cheapest and safest combination of generators and batteries to run?'",
      howItWorks: "It prioritizes renewable wind energy when available, preserves a 35% spinning reserve margin for emergencies, and ensures life-support systems (heaters, life-support) receive highest priority dispatch.",
      keyTakeaway: "Saves up to 18-25% in shipped-in diesel fuel while maintaining continuous life-support priority.",
      icon: <Cpu className="w-8 h-8 text-copper" />,
    },
    {
      title: "6. What Happens During a Failure?",
      badge: "AUTONOMOUS RESILIENCE",
      question: "What if a generator breaks or a blizzard shuts down turbines?",
      plainAnswer: "Polaris-EMS immediately detects the disturbance and shifts into an autonomous protection mode. It sheds non-essential scientific experiments to keep habitat heaters powered.",
      howItWorks: "The 9-dimensional resilience engine continuously computes the station's 'Survival Horizon' (e.g. 84 hours of fuel runway) and highlights the exact bottleneck constraint.",
      keyTakeaway: "Life safety always takes absolute priority (P1 Dominance) over secondary scientific gear.",
      icon: <AlertTriangle className="w-8 h-8 text-copper" />,
    },
    {
      title: "7. Why Should You Trust It?",
      badge: "SCIENTIFIC INTEGRITY",
      question: "Why can polar station commanders trust this software?",
      plainAnswer: "1. Human-in-the-Loop: No physical generator switch is flipped without explicit operator authorization. 2. Scientific Audit: Every single number has an immutable 6-tier provenance trail.",
      howItWorks: "3. Air-Gapped Simulation: The software operates safely in simulation mode with zero live connection to real station SCADA equipment. 4. Complete decision trace lineage for every output.",
      keyTakeaway: "Complete transparency, rigorous physical conservation laws, and zero black-box autonomy.",
      icon: <ShieldCheck className="w-8 h-8 text-moss" />,
    },
  ];

  if (!isOpen) return null;

  const step = steps[currentStep];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-primary/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl bg-surface border border-border rounded-lg shadow-raised overflow-hidden flex flex-col font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="orientation-title"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-border bg-canvas-subtle flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded bg-copper-soft flex items-center justify-center text-copper">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-copper font-bold block">
                60-SECOND ORIENTATION GUIDE
              </span>
              <h3 id="orientation-title" className="text-base font-serif font-bold text-ink-primary">
                Understanding Polaris-EMS in Plain English
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-ink-muted hover:text-ink-primary hover:bg-canvas transition-colors"
            aria-label="Close orientation guide"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Progression Bar */}
        <div className="w-full bg-border-subtle h-1">
          <div
            className="bg-copper h-1 transition-all duration-300"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Step Body */}
        <div className="p-6 sm:p-8 space-y-5 flex-1 overflow-y-auto max-h-[70vh]">
          {/* Top Step Badge & Question */}
          <div className="flex items-start space-x-4">
            <div className="p-3 rounded-lg bg-canvas-subtle border border-border-subtle shrink-0">
              {step.icon}
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-copper-soft text-copper font-bold">
                {step.badge} • STEP {currentStep + 1} OF {steps.length}
              </span>
              <h4 className="text-lg font-serif font-bold text-ink-primary pt-1">
                {step.question}
              </h4>
            </div>
          </div>

          {/* Plain Answer */}
          <div className="p-4 rounded-md bg-canvas-subtle border-l-4 border-l-copper text-sm text-ink-primary leading-relaxed font-sans font-medium">
            {step.plainAnswer}
          </div>

          {/* How It Works */}
          <div className="space-y-1 text-xs text-ink-secondary leading-relaxed font-sans">
            <span className="text-[11px] font-mono text-ink-muted uppercase block font-semibold">
              HOW IT WORKS UNDER THE HOOD:
            </span>
            <p>{step.howItWorks}</p>
          </div>

          {/* Key Takeaway */}
          <div className="p-3 rounded bg-moss-soft/60 border border-moss/30 text-xs text-moss font-sans font-semibold flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-moss" />
            <span>Key Takeaway: {step.keyTakeaway}</span>
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="px-6 py-4 border-t border-border bg-canvas-subtle flex items-center justify-between">
          <button
            type="button"
            disabled={currentStep === 0}
            onClick={() => setCurrentStep(currentStep - 1)}
            className={`inline-flex items-center space-x-1 px-3 py-1.5 rounded font-mono text-xs font-medium transition-colors ${
              currentStep === 0
                ? 'text-ink-subtle cursor-not-allowed'
                : 'text-ink-secondary hover:text-ink-primary hover:bg-canvas border border-border'
            }`}
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>

          <div className="flex items-center space-x-1 text-xs font-mono text-ink-muted">
            <span>{currentStep + 1}</span>
            <span>/</span>
            <span>{steps.length}</span>
          </div>

          {currentStep < steps.length - 1 ? (
            <button
              type="button"
              onClick={() => setCurrentStep(currentStep + 1)}
              className="inline-flex items-center space-x-1 px-4 py-1.5 rounded bg-copper hover:bg-copper-dark text-ink-inverse font-mono text-xs font-semibold shadow-xs transition-colors"
            >
              <span>Next Point</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center space-x-1 px-4 py-1.5 rounded bg-moss hover:bg-moss/90 text-ink-inverse font-mono text-xs font-semibold shadow-xs transition-colors"
            >
              <span>Done • Explore Mission Control</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
