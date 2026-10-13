import { attachAnalyticsSink } from './index.js'

type LogEventMetadata = { [key: string]: boolean | number | undefined }

function dropEvent(_eventName: string, _metadata: LogEventMetadata): void {}

export function initializeAnalyticsGates(): void {}

export function initializeAnalyticsSink(): void {
  attachAnalyticsSink({
    logEvent: dropEvent,
    logEventAsync: async (_eventName, _metadata) => {},
  })
}
