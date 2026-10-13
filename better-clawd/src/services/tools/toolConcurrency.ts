export const DEFAULT_MAX_TOOL_USE_CONCURRENCY = 4

export function getMaxToolUseConcurrency(): number {
  const parsed = parseInt(process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY || '', 10)
  return Number.isFinite(parsed) && parsed > 0
    ? parsed
    : DEFAULT_MAX_TOOL_USE_CONCURRENCY
}
