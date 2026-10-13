import { unsupportedEntrypoint } from '../utils/unsupportedEntrypoint.js'

export async function environmentRunnerMain(): Promise<never> {
  return unsupportedEntrypoint('claude-cli environment-runner')
}
