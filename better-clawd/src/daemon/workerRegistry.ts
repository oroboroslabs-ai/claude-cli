import { unsupportedEntrypoint } from '../utils/unsupportedEntrypoint.js'

export async function runDaemonWorker(kind?: string): Promise<never> {
  return unsupportedEntrypoint(
    kind ? `claude-cli --daemon-worker ${kind}` : 'claude-cli --daemon-worker',
  )
}
