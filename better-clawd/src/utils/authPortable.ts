import { execa } from 'execa'
import { getMacOsKeychainStorageServiceNames } from 'src/utils/secureStorage/macOsKeychainHelpers.js'

export async function maybeRemoveApiKeyFromMacOSKeychainThrows(): Promise<void> {
  if (process.platform === 'darwin') {
    let deletedAny = false
    for (const storageServiceName of getMacOsKeychainStorageServiceNames()) {
      const result = await execa(
        `security delete-generic-password -a $USER -s "${storageServiceName}"`,
        { shell: true, reject: false },
      )
      if (result.exitCode === 0) {
        deletedAny = true
      }
    }
    if (!deletedAny) {
      throw new Error('Failed to delete keychain entry')
    }
  }
}

export function normalizeApiKeyForConfig(apiKey: string): string {
  return apiKey.slice(-20)
}
