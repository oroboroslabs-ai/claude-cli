import { unsupportedEntrypoint } from '../utils/unsupportedEntrypoint.js'

export async function selfHostedRunnerMain(): Promise<never> {
  return unsupportedEntrypoint('claude-cli self-hosted-runner')
}
