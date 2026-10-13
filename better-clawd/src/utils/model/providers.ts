import type { AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS } from '../../services/analytics/index.js'
import { isEnvTruthy } from '../envUtils.js'

export type APIProvider =
  | 'firstParty'
  | 'openrouter'
  | 'openai'
  | 'firepass'
  | 'bedrock'
  | 'vertex'
  | 'foundry'

function getStoredProviderPreference(): APIProvider | null {
  try {
    // Read the global config file directly so provider selection works even
    // before the guarded config loader is enabled during startup.
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { readFileSync } = require('fs') as typeof import('fs')
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { getGlobalClaudeFile } =
      require('../env.js') as typeof import('../env.js')
    const raw = readFileSync(getGlobalClaudeFile(), 'utf8')
    const config = JSON.parse(raw) as {
      authProvider?: 'anthropic' | 'openrouter' | 'openai' | 'firepass'
      openRouterApiKey?: string
      openAiApiKey?: string
      openAiAccessToken?: string
      firepassApiKey?: string
    }

    switch (config.authProvider) {
      case 'openrouter':
        return config.openRouterApiKey ? 'openrouter' : null
      case 'openai':
        return config.openAiApiKey || config.openAiAccessToken
          ? 'openai'
          : null
      case 'firepass':
        return config.firepassApiKey ? 'firepass' : null
      case 'anthropic':
        return 'firstParty'
      default:
        return null
    }
  } catch {
    return null
  }
}

function getExplicitProviderOverride(): APIProvider | null {
  const rawProvider =
    process.env.CLAUDE_CLI_API_PROVIDER ??
    process.env.CLAUDE_CODE_API_PROVIDER
  switch (rawProvider?.toLowerCase()) {
    case 'anthropic':
    case 'firstparty':
    case 'first_party':
    case 'first-party':
      return 'firstParty'
    case 'openrouter':
      return 'openrouter'
    case 'openai':
      return 'openai'
    case 'firepass':
    case 'fire-pass':
    case 'fire_pass':
      return 'firepass'
    case 'bedrock':
      return 'bedrock'
    case 'vertex':
      return 'vertex'
    case 'foundry':
      return 'foundry'
    default:
      return null
  }
}

export function isOpenRouterBaseUrl(baseUrl?: string | null): boolean {
  if (!baseUrl) {
    return false
  }
  try {
    return new URL(baseUrl).host === 'openrouter.ai'
  } catch {
    return false
  }
}

export function isOpenRouterConfigured(): boolean {
  return (
    getExplicitProviderOverride() === 'openrouter' ||
    Boolean(process.env.OPENROUTER_API_KEY) ||
    isOpenRouterBaseUrl(process.env.OPENROUTER_BASE_URL) ||
    isOpenRouterBaseUrl(process.env.ANTHROPIC_BASE_URL)
  )
}

export function isOpenAIConfigured(): boolean {
  return (
    getExplicitProviderOverride() === 'openai' ||
    Boolean(process.env.OPENAI_API_KEY) ||
    Boolean(process.env.OPENAI_BASE_URL) ||
    Boolean(process.env.OPENAI_ACCESS_TOKEN) ||
    Boolean(process.env.CODEX_ACCESS_TOKEN)
  )
}

export function isFirepassBaseUrl(baseUrl?: string | null): boolean {
  if (!baseUrl) {
    return false
  }
  try {
    const host = new URL(baseUrl).host
    return host === 'api.fireworks.ai'
  } catch {
    return false
  }
}

export function isFirepassConfigured(): boolean {
  return (
    getExplicitProviderOverride() === 'firepass' ||
    Boolean(process.env.FIREPASS_API_KEY) ||
    Boolean(process.env.FIREWORKS_API_KEY) ||
    isFirepassBaseUrl(process.env.FIREPASS_BASE_URL) ||
    isFirepassBaseUrl(process.env.ANTHROPIC_BASE_URL)
  )
}

export function getOpenRouterBaseUrl(): string {
  const configuredBaseUrl = process.env.OPENROUTER_BASE_URL
  const fallbackBaseUrl = 'https://openrouter.ai/api'
  if (!configuredBaseUrl) {
    return fallbackBaseUrl
  }

  try {
    const url = new URL(configuredBaseUrl)

    if (url.host === 'openrouter.ai') {
      const normalizedPath = url.pathname.replace(/\/+$/, '')
      if (normalizedPath === '' || normalizedPath === '/') {
        url.pathname = '/api'
      } else if (normalizedPath === '/api/v1') {
        // Anthropic SDK appends /v1/messages itself, so OpenRouter's SDK base
        // must stop at /api rather than /api/v1.
        url.pathname = '/api'
      }
    }

    return url.toString().replace(/\/$/, '')
  } catch {
    return configuredBaseUrl
  }
}

export function getOpenAIBaseUrl(): string {
  return process.env.OPENAI_BASE_URL ?? 'https://api.openai.com/v1'
}

/**
 * Get the FirePass base URL for Anthropic-compatible API.
 * FirePass uses Fireworks AI's inference endpoint with Anthropic compatibility.
 * Default: https://api.fireworks.ai/inference (Anthropic SDK appends /v1/messages)
 */
export function getFirepassBaseUrl(): string {
  const configuredBaseUrl = process.env.FIREPASS_BASE_URL
  if (!configuredBaseUrl) {
    return 'https://api.fireworks.ai/inference'
  }

  try {
    const url = new URL(configuredBaseUrl)

    // Normalize path for Anthropic SDK compatibility
    // SDK appends /v1/messages, so base should be /inference not /inference/v1
    if (url.host === 'api.fireworks.ai') {
      const normalizedPath = url.pathname.replace(/\/+$/, '')
      if (normalizedPath === '/inference/v1' || normalizedPath === '/v1') {
        url.pathname = '/inference'
      }
    }

    return url.toString().replace(/\/$/, '')
  } catch {
    return configuredBaseUrl
  }
}

export function getAPIProvider(): APIProvider {
  const explicitProvider = getExplicitProviderOverride()
  if (explicitProvider) {
    return explicitProvider
  }

  return isEnvTruthy(process.env.CLAUDE_CODE_USE_BEDROCK)
    ? 'bedrock'
    : isEnvTruthy(process.env.CLAUDE_CODE_USE_VERTEX)
      ? 'vertex'
      : isEnvTruthy(process.env.CLAUDE_CODE_USE_FOUNDRY)
        ? 'foundry'
        : isOpenAIConfigured()
          ? 'openai'
          : isFirepassConfigured()
            ? 'firepass'
            : isOpenRouterConfigured()
              ? 'openrouter'
              : getStoredProviderPreference() ?? 'firstParty'
}

export function getAPIProviderForStatsig(): AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS {
  return getAPIProvider() as AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS
}

export function isAnthropicCompatibleProvider(
  provider: APIProvider = getAPIProvider(),
): boolean {
  return provider !== 'openai'
}

/**
 * Check if ANTHROPIC_BASE_URL is a first-party Anthropic API URL.
 * Returns true if not set (default API) or points to api.anthropic.com
 * (or api-staging.anthropic.com for ant users).
 */
export function isFirstPartyAnthropicBaseUrl(): boolean {
  const baseUrl = process.env.ANTHROPIC_BASE_URL
  if (!baseUrl) {
    return true
  }
  try {
    const host = new URL(baseUrl).host
    const allowedHosts = ['api.anthropic.com']
    if (process.env.USER_TYPE === 'ant') {
      allowedHosts.push('api-staging.anthropic.com')
    }
    return allowedHosts.includes(host)
  } catch {
    return false
  }
}
