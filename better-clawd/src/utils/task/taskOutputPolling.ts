export const ACTIVE_TASK_OUTPUT_POLL_INTERVAL_MS = 250
const IDLE_TASK_OUTPUT_POLL_INTERVAL_MS = 1000
const MAX_TASK_OUTPUT_POLL_INTERVAL_MS = 4000

export function getNextTaskOutputPollIntervalMs(
  currentIntervalMs: number,
  sawActivity: boolean,
): number {
  if (sawActivity) {
    return ACTIVE_TASK_OUTPUT_POLL_INTERVAL_MS
  }
  if (currentIntervalMs < IDLE_TASK_OUTPUT_POLL_INTERVAL_MS) {
    return IDLE_TASK_OUTPUT_POLL_INTERVAL_MS
  }
  return Math.min(MAX_TASK_OUTPUT_POLL_INTERVAL_MS, currentIntervalMs * 2)
}
