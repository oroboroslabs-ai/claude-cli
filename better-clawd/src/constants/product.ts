export const PRODUCT_NAME = 'Oroboros-Anthropic Claude CLI'
export const LEGACY_PRODUCT_NAME = 'Claude Code'
export const PRODUCT_SLUG = 'claude-cli'
export const LEGACY_PRODUCT_SLUG = 'claude-code'
export const CLI_BINARY_NAME = 'claude-cli'
export const LEGACY_CLI_BINARY_NAME = 'claude'
export const PRODUCT_CONFIG_DIRNAME = '.claude-cli'
export const LEGACY_PRODUCT_CONFIG_DIRNAME = '.claude'
export const PRODUCT_CONFIG_ENV_VAR = 'CLAUDE_CLI_CONFIG_DIR'
export const LEGACY_PRODUCT_CONFIG_ENV_VAR = 'CLAUDE_CONFIG_DIR'
export const PRODUCT_URL = 'https://github.com/oroboroslabs-ai/claude-cli'
export const PRODUCT_ISSUES_URL =
  'https://github.com/oroboroslabs-ai/claude-cli/issues'
export const PRODUCT_NOREPLY_EMAIL = 'noreply@claude-cli.invalid'

// Anthropic web URLs are kept for the Anthropic provider and remote sessions.
export const ANTHROPIC_APP_BASE_URL = 'https://claude.ai'
export const ANTHROPIC_APP_STAGING_BASE_URL =
  'https://claude-ai.staging.ant.dev'
export const ANTHROPIC_APP_LOCAL_BASE_URL = 'http://localhost:4000'

// Backward-compatible aliases while the Anthropic provider is still supported.
export const CLAUDE_AI_BASE_URL = ANTHROPIC_APP_BASE_URL
export const CLAUDE_AI_STAGING_BASE_URL = ANTHROPIC_APP_STAGING_BASE_URL
export const CLAUDE_AI_LOCAL_BASE_URL = ANTHROPIC_APP_LOCAL_BASE_URL

export function getConfiguredProductConfigDir(): string | undefined {
  return process.env[PRODUCT_CONFIG_ENV_VAR]
}

/**
 * Determine if we're in a staging environment for remote sessions.
 * Checks session ID format and ingress URL.
 */
export function isRemoteSessionStaging(
  sessionId?: string,
  ingressUrl?: string,
): boolean {
  return (
    sessionId?.includes('_staging_') === true ||
    ingressUrl?.includes('staging') === true
  )
}

/**
 * Determine if we're in a local-dev environment for remote sessions.
 * Checks session ID format (e.g. `session_local_...`) and ingress URL.
 */
export function isRemoteSessionLocal(
  sessionId?: string,
  ingressUrl?: string,
): boolean {
  return (
    sessionId?.includes('_local_') === true ||
    ingressUrl?.includes('localhost') === true
  )
}

/**
 * Get the base URL for Claude AI based on environment.
 */
export function getClaudeAiBaseUrl(
  sessionId?: string,
  ingressUrl?: string,
): string {
  if (isRemoteSessionLocal(sessionId, ingressUrl)) {
    return ANTHROPIC_APP_LOCAL_BASE_URL
  }
  if (isRemoteSessionStaging(sessionId, ingressUrl)) {
    return ANTHROPIC_APP_STAGING_BASE_URL
  }
  return ANTHROPIC_APP_BASE_URL
}

/**
 * Get the full session URL for a remote session.
 *
 * The cse_→session_ translation is a temporary shim gated by
 * tengu_bridge_repl_v2_cse_shim_enabled (see isCseShimEnabled). Worker
 * endpoints (/v1/code/sessions/{id}/worker/*) want `cse_*` but the claude.ai
 * frontend currently routes on `session_*` (compat/convert.go:27 validates
 * TagSession). Same UUID body, different tag prefix. Once the server tags by
 * environment_kind and the frontend accepts `cse_*` directly, flip the gate
 * off. No-op for IDs already in `session_*` form. See toCompatSessionId in
 * src/bridge/sessionIdCompat.ts for the canonical helper (lazy-required here
 * to keep constants/ leaf-of-DAG at module-load time).
 */
export function getRemoteSessionUrl(
  sessionId: string,
  ingressUrl?: string,
): string {
  /* eslint-disable @typescript-eslint/no-require-imports */
  const { toCompatSessionId } =
    require('../bridge/sessionIdCompat.js') as typeof import('../bridge/sessionIdCompat.js')
  /* eslint-enable @typescript-eslint/no-require-imports */
  const compatId = toCompatSessionId(sessionId)
  const baseUrl = getClaudeAiBaseUrl(compatId, ingressUrl)
  return `${baseUrl}/code/${compatId}`
}
