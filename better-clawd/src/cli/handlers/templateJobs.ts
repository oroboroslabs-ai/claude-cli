import { unsupportedEntrypoint } from '../../utils/unsupportedEntrypoint.js'

export async function templatesMain(): Promise<never> {
  return unsupportedEntrypoint('claude-cli new')
}
