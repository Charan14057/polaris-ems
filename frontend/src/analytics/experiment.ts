/**
 * POLARIS-EMS A/B TESTING EXPERIMENTAL HARNESS
 * Supports deterministic bucketing between 'control', 'variant_a', 'variant_b'.
 * Default behavior: Inactive unless explicitly enabled for human-in-the-loop evaluation.
 */

export type ExperimentVariant = 'control' | 'variant_a' | 'variant_b';

export interface ExperimentConfig {
  experimentId: string;
  enabled: boolean;
  defaultVariant: ExperimentVariant;
}

const EXPERIMENT_STORAGE_KEY = 'polaris_exp_assignments';

export class ExperimentManager {
  private assignments: Record<string, ExperimentVariant> = {};

  constructor() {
    try {
      const stored = localStorage.getItem(EXPERIMENT_STORAGE_KEY);
      if (stored) {
        this.assignments = JSON.parse(stored);
      }
    } catch {
      this.assignments = {};
    }
  }

  getVariant(config: ExperimentConfig): ExperimentVariant {
    if (!config.enabled) {
      return config.defaultVariant;
    }

    if (this.assignments[config.experimentId]) {
      return this.assignments[config.experimentId];
    }

    // Deterministic random assignment
    const variants: ExperimentVariant[] = ['control', 'variant_a', 'variant_b'];
    const chosen = variants[Math.floor(Math.random() * variants.length)];
    this.assignments[config.experimentId] = chosen;

    try {
      localStorage.setItem(EXPERIMENT_STORAGE_KEY, JSON.stringify(this.assignments));
    } catch {
      // Ignored in restricted environments
    }

    return chosen;
  }
}

export const experimentManager = new ExperimentManager();
