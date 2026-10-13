import { unsupportedEntrypoint } from '../utils/unsupportedEntrypoint.js'

export async function psHandler(): Promise<never> {
  return unsupportedEntrypoint('claude-cli ps')
}

export async function logsHandler(): Promise<never> {
  return unsupportedEntrypoint('claude-cli logs')
}

export async function attachHandler(): Promise<never> {
  return unsupportedEntrypoint('claude-cli attach')
}

export async function killHandler(): Promise<never> {
  return unsupportedEntrypoint('claude-cli kill')
}

export async function handleBgFlag(): Promise<never> {
  return unsupportedEntrypoint('claude-cli --bg')
}
