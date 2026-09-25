import React, { useState } from 'react';
import { HelpCircle, Info } from 'lucide-react';

export const JARGON_DICTIONARY: Record<string, { term: string; plain: string; context: string }> = {
  'Digital Twin': {
    term: 'Digital Twin',
    plain: "A computer simulation that mimics how the polar station's power and heating equipment physically behave in real time.",
    context: "Allows engineers to safely test decisions before touching real hardware.",
  },
  'MILP Optimizer': {
    term: 'MILP (Optimization Engine)',
    plain: 'A mathematical problem-solver that calculates the safest and most fuel-efficient schedule for generators and batteries.',
    context: 'Guarantees that life-saving heaters never run out of power.',
  },
  'Optimization': {
    term: 'Optimization Engine',
    plain: 'A mathematical computer program that automatically calculates the best balance of generators, batteries, and renewables.',
    context: 'Balancing lowest fuel consumption with highest crew safety.',
  },
  'Forecast': {
    term: 'Energy & Weather Forecast',
    plain: "The AI's prediction of upcoming wind speed, solar light, and electrical demand over the next 48 to 168 hours.",
    context: 'Gives the crew advance warning before severe weather hits.',
  },
  'Resilience': {
    term: 'Resilience (Survival Capacity)',
    plain: 'A measure of how many hours the station can survive and keep crew warm if fuel deliveries are cut off or generators fail.',
    context: 'Identifies the single weakest link (e.g., fuel tank vs battery bank).',
  },
  'Telemetry': {
    term: 'Telemetry',
    plain: 'Live sensor readings sent from physical equipment (voltages, temperatures, fuel levels, wind speeds).',
    context: 'Data used to assess the current health of the station.',
  },
  'HIL': {
    term: 'HIL (Hardware-in-the-Loop)',
    plain: 'A laboratory test bench where software talks to real microchips and relays in a controlled room, rather than a remote Antarctic outpost.',
    context: 'Tests real controllers without risking station blackout.',
  },
  'Hardware-in-the-Loop': {
    term: 'Hardware-in-the-Loop (HIL)',
    plain: 'A laboratory test bench where software talks to real microchips and relays in a controlled room, rather than a remote Antarctic outpost.',
    context: 'Tests real controllers without risking station blackout.',
  },
  'SCADA': {
    term: 'SCADA (Industrial Control Link)',
    plain: 'Supervisory Control and Data Acquisition: The heavy industrial network that controls physical polar generators and breakers.',
    context: 'Polaris-EMS is strictly air-gapped from live polar SCADA to prevent unauthorized actuation.',
  },
  'Edge Computing': {
    term: 'Edge Computing',
    plain: 'Running computation directly on computers located inside the polar station, rather than depending on a fragile satellite link to the cloud.',
    context: 'Ensures the station stays safe even during complete satellite blackout.',
  },
  'Provenance': {
    term: 'Data Provenance',
    plain: 'The audited origin of a data point (e.g. verified sensor reading vs AI estimate vs simulation test).',
    context: 'Guarantees the crew knows whether a number is real or simulated.',
  },
  'Quantile Interval': {
    term: 'Quantile Interval (P10–P90)',
    plain: 'A range of possibilities. P50 is the most likely outcome, P10 is a conservative low estimate, and P90 is a high estimate.',
    context: 'Helps operators plan for the worst-case weather scenarios.',
  },
  'P10–P90': {
    term: 'P10–P90 Uncertainty Band',
    plain: 'The 80% confidence window: there is an 80% chance the actual value will fall between these two numbers.',
    context: 'Acknowledges real-world uncertainty in weather forecasting.',
  },
  'Spinning Reserve': {
    term: 'Spinning Reserve',
    plain: 'Extra generator capacity kept warm and running ready to take over in seconds if wind generation suddenly crashes.',
    context: 'Crucial for polar life-support continuity.',
  },
  'State of Charge': {
    term: 'Battery SOC (State of Charge)',
    plain: 'The percentage of usable energy left in the battery storage bank, like a smartphone battery percentage.',
    context: '100% is full; safe emergency minimum is usually 20-30%.',
  },
  'Air-Gap': {
    term: 'Simulation Air-Gap',
    plain: 'A strict physical barrier ensuring software simulations cannot send accidental control signals to real station machinery.',
    context: 'Ensures safety and absolute operational containment.',
  },
};

interface JargonTooltipProps {
  term: keyof typeof JARGON_DICTIONARY | string;
  children?: React.ReactNode;
  className?: string;
  showIcon?: boolean;
}

export const JargonTooltip: React.FC<JargonTooltipProps> = ({
  term,
  children,
  className = '',
  showIcon = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const info = JARGON_DICTIONARY[term] || {
    term,
    plain: `A technical operational parameter used in polar energy management.`,
    context: `Essential for automated monitoring and station resilience.`,
  };

  return (
    <span className="relative inline-flex items-baseline group">
      <span
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className={`cursor-help border-b border-dotted border-copper/70 text-ink-primary hover:text-copper transition-colors inline-flex items-center gap-0.5 ${className}`}
        aria-label={`Plain language explanation for ${info.term}`}
      >
        <span>{children || term}</span>
        {showIcon && (
          <HelpCircle className="w-3 h-3 text-copper/70 inline-block shrink-0 ml-0.5" />
        )}
      </span>

      {isOpen && (
        <span
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 sm:w-80 p-3 bg-surface rounded border border-border shadow-sheet text-left font-sans text-xs transition-opacity duration-150 animate-in fade-in"
        >
          <span className="block font-mono text-[10px] uppercase tracking-wider text-copper font-bold mb-1">
            PLAIN-LANGUAGE GUIDE
          </span>
          <span className="block font-semibold text-ink-primary text-xs mb-1">
            {info.term}
          </span>
          <span className="block text-ink-secondary text-[11px] leading-relaxed mb-2 font-normal">
            {info.plain}
          </span>
          <span className="block text-[10px] text-ink-muted bg-canvas-subtle p-1.5 rounded border border-border-subtle font-mono">
            💡 <strong className="text-ink-secondary">Why it matters:</strong> {info.context}
          </span>
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-border" />
        </span>
      )}
    </span>
  );
};
