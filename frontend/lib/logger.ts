type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  context?: Record<string, unknown>
  error?: Error
}

class Logger {
  private isDevelopment = process.env.NODE_ENV === 'development'
  private logs: LogEntry[] = []
  private maxLogs = 100

  /**
   * Log a debug message
   */
  debug(message: string, context?: Record<string, unknown>): void {
    this.log('debug', message, context)
  }

  /**
   * Log an info message
   */
  info(message: string, context?: Record<string, unknown>): void {
    this.log('info', message, context)
  }

  /**
   * Log a warning message
   */
  warn(message: string, context?: Record<string, unknown>): void {
    this.log('warn', message, context)
  }

  /**
   * Log an error message
   */
  error(message: string, error?: Error, context?: Record<string, unknown>): void {
    this.log('error', message, { ...context, error })
  }

  /**
   * Log API request
   */
  logRequest(method: string, url: string, data?: unknown): void {
    this.debug(`API Request: ${method} ${url}`, { method, url, data })
  }

  /**
   * Log API response
   */
  logResponse(
    method: string,
    url: string,
    status: number,
    duration: number,
    data?: unknown
  ): void {
    const level = status >= 400 ? 'error' : 'debug'
    this.log(level, `API Response: ${method} ${url} - ${status} (${duration}ms)`, {
      method,
      url,
      status,
      duration,
      data: this.isDevelopment ? data : undefined,
    })
  }

  /**
   * Log API error
   */
  logApiError(
    method: string,
    url: string,
    error: Error,
    duration: number
  ): void {
    this.error(`API Error: ${method} ${url} (${duration}ms)`, error, {
      method,
      url,
      duration,
    })
  }

  /**
   * Log user action
   */
  logAction(action: string, context?: Record<string, unknown>): void {
    this.info(`User Action: ${action}`, context)
  }

  /**
   * Log WebSocket event
   */
  logWebSocket(event: string, context?: Record<string, unknown>): void {
    this.debug(`WebSocket: ${event}`, context)
  }

  /**
   * Get recent logs
   */
  getRecentLogs(limit?: number): LogEntry[] {
    return limit ? this.logs.slice(-limit) : this.logs
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = []
  }

  /**
   * Export logs as JSON
   */
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }

  /**
   * Core logging method
   */
  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>
  ): void {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
    }

    // Store in memory (with size limit)
    this.logs.push(entry)
    if (this.logs.length > this.maxLogs) {
      this.logs.shift()
    }

    // Console output in development
    if (this.isDevelopment) {
      this.consoleLog(entry)
    }

    // Send to monitoring service in production
    if (!this.isDevelopment && level === 'error') {
      this.sendToMonitoring(entry)
    }
  }

  /**
   * Output to console with formatting
   */
  private consoleLog(entry: LogEntry): void {
    const { level, message, context, timestamp } = entry
    const timeStr = new Date(timestamp).toLocaleTimeString()

    const styles: Record<LogLevel, string> = {
      debug: 'color: #888',
      info: 'color: #2196F3',
      warn: 'color: #FF9800',
      error: 'color: #F44336; font-weight: bold',
    }

    if (context) {
      // Extract and format error if present
      const { error, ...restContext } = context
      
      if (error instanceof Error) {
        // Log error separately for better formatting
        const hasContext = Object.keys(restContext).length > 0
        console[level](
          `%c[${timeStr}] ${message}`,
          styles[level]
        )
        if (hasContext) {
          console[level]('Context:', restContext)
        }
        
        // Build error details object
        const errorDetails: Record<string, unknown> = {
          name: error.name,
          message: error.message,
        }
        const errorWithCode = error as { statusCode?: number; code?: string }
        if (errorWithCode.statusCode !== undefined) {
          errorDetails.statusCode = errorWithCode.statusCode
        }
        if (errorWithCode.code !== undefined) {
          errorDetails.code = errorWithCode.code
        }
        
        console[level]('Error:', errorDetails)
        if (error.stack && this.isDevelopment) {
          console[level]('Stack:', error.stack)
        }
      } else {
        console[level](
          `%c[${timeStr}] ${message}`,
          styles[level],
          context
        )
      }
    } else {
      console[level](`%c[${timeStr}] ${message}`, styles[level])
    }
  }

  /**
   * Send logs to monitoring service (e.g., Sentry, LogRocket)
   */
  private sendToMonitoring(entry: LogEntry): void {
    // Implement integration with monitoring service
    // Example: Sentry.captureException(entry)
    
    // For now, just log to console in production
    console.error('[Monitoring]', entry)
  }
}

// Export singleton instance
export const logger = new Logger()

/**
 * Performance measurement helper
 */
export class PerformanceTimer {
  private startTime: number

  constructor(private label: string) {
    this.startTime = performance.now()
    logger.debug(`⏱️ ${label} started`)
  }

  end(context?: Record<string, unknown>): number {
    const duration = Math.round(performance.now() - this.startTime)
    logger.debug(`⏱️ ${this.label} completed in ${duration}ms`, context)
    return duration
  }
}

/**
 * Create a performance timer
 */
export function createTimer(label: string): PerformanceTimer {
  return new PerformanceTimer(label)
}
