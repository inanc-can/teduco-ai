/**
 * Analytics and telemetry tracking for AI editor features
 * Tracks suggestion acceptance, rejection, and position recovery metrics
 */

interface SuggestionMetrics {
  suggestionId: string;
  category: string;
  confidence: number;
  action: 'applied' | 'rejected' | 'position_recovery_failed';
  timeToAction?: number; // milliseconds from creation to action
  positionVerified?: boolean;
  fuzzyMatchUsed?: boolean;
  fuzzyMatchScore?: number;
  textLength?: number;
  metadata?: Record<string, unknown>;
}

class Analytics {
  private enabled: boolean;
  
  constructor() {
    // Only enable in production or when explicitly enabled
    this.enabled = process.env.NODE_ENV === 'production' || 
                   process.env.NEXT_PUBLIC_ANALYTICS_ENABLED === 'true';
  }

  /**
   * Track suggestion application or rejection
   */
  trackSuggestion(metrics: SuggestionMetrics) {
    if (!this.enabled) {
      console.log('[Analytics] (disabled)', metrics);
      return;
    }

    // In production, send to analytics service
    // For now, log to console
    console.log('[Analytics] Suggestion event:', {
      ...metrics,
      timestamp: new Date().toISOString(),
    });

    // TODO: Send to actual analytics service
    // Example: posthog, mixpanel, amplitude, etc.
    // window.posthog?.capture('suggestion_event', metrics);
  }

  /**
   * Track position recovery failures for debugging
   */
  trackPositionRecoveryFailed(data: {
    suggestionId: string;
    method: 'exact' | 'fuzzy' | 'anchor';
    originalText: string;
    textLength: number;
    suggestionAge?: number; // milliseconds since suggestion created
    hasContext: boolean;
  }) {
    if (!this.enabled) {
      console.log('[Analytics] Position recovery failed (disabled)', data);
      return;
    }

    console.warn('[Analytics] Position recovery failed:', {
      ...data,
      timestamp: new Date().toISOString(),
    });

    // Track for debugging and improving position recovery algorithm
  }

  /**
   * Track analysis performance
   */
  trackAnalysis(data: {
    letterId: string;
    contentLength: number;
    paragraphCount: number;
    cachedParagraphs?: number;
    analyzedParagraphs?: number;
    suggestionCount: number;
    durationMs: number;
    phase: 'grammar' | 'strategic' | 'both';
  }) {
    if (!this.enabled) {
      console.log('[Analytics] Analysis (disabled)', data);
      return;
    }

    console.log('[Analytics] Analysis completed:', {
      ...data,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Track suggestion acceptance rate over time
   */
  trackAcceptanceRate(data: {
    totalSuggestions: number;
    appliedCount: number;
    rejectedCount: number;
    ignoredCount: number;
    sessionDurationMs: number;
  }) {
    if (!this.enabled) {
      console.log('[Analytics] Acceptance rate (disabled)', data);
      return;
    }

    const acceptanceRate = data.totalSuggestions > 0
      ? data.appliedCount / data.totalSuggestions
      : 0;

    console.log('[Analytics] Acceptance rate:', {
      ...data,
      acceptanceRate: `${(acceptanceRate * 100).toFixed(1)}%`,
      timestamp: new Date().toISOString(),
    });
  }
}

// Singleton instance
export const analytics = new Analytics();

// Helper functions for common tracking patterns
export function trackSuggestionApplied(
  suggestionId: string,
  category: string,
  confidence: number,
  createdAt: number,
  positionVerified: boolean,
  fuzzyMatchUsed?: boolean,
  fuzzyMatchScore?: number
) {
  analytics.trackSuggestion({
    suggestionId,
    category,
    confidence,
    action: 'applied',
    timeToAction: Date.now() - createdAt,
    positionVerified,
    fuzzyMatchUsed,
    fuzzyMatchScore,
  });
}

export function trackSuggestionRejected(
  suggestionId: string,
  category: string,
  confidence: number,
  createdAt: number
) {
  analytics.trackSuggestion({
    suggestionId,
    category,
    confidence,
    action: 'rejected',
    timeToAction: Date.now() - createdAt,
  });
}

export function trackPositionRecoveryFailed(
  suggestionId: string,
  originalText: string,
  hasContext: boolean,
  suggestionAge?: number
) {
  analytics.trackPositionRecoveryFailed({
    suggestionId,
    method: hasContext ? 'anchor' : 'exact',
    originalText,
    textLength: originalText.length,
    suggestionAge,
    hasContext,
  });
}
