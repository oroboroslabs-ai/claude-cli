export type CacheEditsBlock = {
  type: 'cache_edits'
  delete_tool_result_ids: string[]
}

export type PinnedCacheEdits = {
  userMessageIndex: number
  block: CacheEditsBlock
}

export type CachedMCState = {
  registeredTools: Set<string>
  deletedRefs: Set<string>
  toolOrder: string[]
  pinnedEdits: PinnedCacheEdits[]
}

export function isCachedMicrocompactEnabled(): boolean {
  return false
}

export function isModelSupportedForCacheEditing(_model: string): boolean {
  return false
}

export function getCachedMCConfig() {
  return {
    triggerThreshold: 0,
    keepRecent: 0,
    supportedModels: [] as string[],
  }
}

export function createCachedMCState(): CachedMCState {
  return {
    registeredTools: new Set(),
    deletedRefs: new Set(),
    toolOrder: [],
    pinnedEdits: [],
  }
}

export function registerToolResult(
  state: CachedMCState,
  toolUseId: string,
): void {
  if (state.registeredTools.has(toolUseId)) {
    return
  }
  state.registeredTools.add(toolUseId)
  state.toolOrder.push(toolUseId)
}

export function registerToolMessage(
  _state: CachedMCState,
  _groupIds: string[],
): void {}

export function getToolResultsToDelete(_state: CachedMCState): string[] {
  return []
}

export function createCacheEditsBlock(
  _state: CachedMCState,
  toolIds: string[],
): CacheEditsBlock | null {
  if (toolIds.length === 0) {
    return null
  }
  return {
    type: 'cache_edits',
    delete_tool_result_ids: toolIds,
  }
}

export function markToolsSentToAPI(_state: CachedMCState): void {}

export function resetCachedMCState(state: CachedMCState): void {
  state.registeredTools.clear()
  state.deletedRefs.clear()
  state.toolOrder.length = 0
  state.pinnedEdits.length = 0
}
