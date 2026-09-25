/**
 * POLARIS-EMS ANALYTICS DISPATCHER
 * Strictly in-memory and local. No third-party network beacons or external tracker dependencies.
 */

import { AnalyticsEvent, AnalyticsEventType } from './events';

export interface AnalyticsOptions {
  enabled?: boolean;
  debug?: boolean;
}

class PolarisAnalytics {
  private enabled: boolean = false;
  private debug: boolean = false;
  private buffer: AnalyticsEvent[] = [];
  private readonly maxBufferSize: number = 200;

  init(options: AnalyticsOptions = {}) {
    this.enabled = options.enabled ?? false;
    this.debug = options.debug ?? false;
  }

  track(type: AnalyticsEventType, properties?: Record<string, any>) {
    const event: AnalyticsEvent = {
      type,
      timestamp: new Date().toISOString(),
      properties,
    };

    if (this.buffer.length >= this.maxBufferSize) {
      this.buffer.shift();
    }
    this.buffer.push(event);

    if (this.debug) {
      // eslint-disable-next-line no-console
      console.debug('[POLARIS-ANALYTICS]', type, properties);
    }
  }

  getRecentEvents(): readonly AnalyticsEvent[] {
    return this.buffer;
  }

  clear() {
    this.buffer = [];
  }
}

export const analytics = new PolarisAnalytics();
