import { feature } from 'bun:bundle'
import * as React from 'react'
import { useMemo, useState } from 'react'
import { resetCostState } from '../../bootstrap/state.js'
import {
  clearTrustedDeviceToken,
  enrollTrustedDevice,
} from '../../bridge/trustedDevice.js'
import type { LocalJSXCommandContext } from '../../commands.js'
import { ConfigurableShortcutHint } from '../../components/ConfigurableShortcutHint.js'
import { ConsoleOAuthFlow } from '../../components/ConsoleOAuthFlow.js'
import { Select } from '../../components/CustomSelect/select.js'
import { Dialog } from '../../components/design-system/Dialog.js'
import { FirepassLoginFlow } from '../../components/FirepassLoginFlow.js'
import { OpenAILoginFlow } from '../../components/OpenAILoginFlow.js'
import { OpenRouterLoginFlow } from '../../components/OpenRouterLoginFlow.js'
import { useMainLoopModel } from '../../hooks/useMainLoopModel.js'
import { Box, Text } from '../../ink.js'
import { refreshGrowthBookAfterAuthChange } from '../../services/analytics/growthbook.js'
import { refreshPolicyLimits } from '../../services/policyLimits/index.js'
import { refreshRemoteManagedSettings } from '../../services/remoteManagedSettings/index.js'
import type { LocalJSXCommandOnDone } from '../../types/command.js'
import { getConfiguredAuthProvider } from '../../utils/auth.js'
import { stripSignatureBlocks } from '../../utils/messages.js'
import {
  checkAndDisableAutoModeIfNeeded,
  checkAndDisableBypassPermissionsIfNeeded,
  resetAutoModeGateCheck,
  resetBypassPermissionsCheck,
} from '../../utils/permissions/bypassPermissionsKillswitch.js'
import { resetUserCache } from '../../utils/user.js'

type AuthProviderChoice = 'anthropic' | 'openai' | 'openrouter' | 'firepass'

export async function call(
  onDone: LocalJSXCommandOnDone,
  context: LocalJSXCommandContext,
): Promise<React.ReactNode> {
  return (
    <Login
      onDone={async success => {
        context.onChangeAPIKey()
        // Signature-bearing blocks are tied to the active auth state.
        context.setMessages(stripSignatureBlocks)

        if (success) {
          resetCostState()
          void refreshRemoteManagedSettings()
          void refreshPolicyLimits()
          resetUserCache()
          refreshGrowthBookAfterAuthChange()
          clearTrustedDeviceToken()
          void enrollTrustedDevice()

          resetBypassPermissionsCheck()
          const appState = context.getAppState()
          void checkAndDisableBypassPermissionsIfNeeded(
            appState.toolPermissionContext,
            context.setAppState,
          )

          if (feature('TRANSCRIPT_CLASSIFIER')) {
            resetAutoModeGateCheck()
            void checkAndDisableAutoModeIfNeeded(
              appState.toolPermissionContext,
              context.setAppState,
              appState.fastMode,
            )
          }

          context.setAppState(prev => ({
            ...prev,
            authVersion: prev.authVersion + 1,
          }))
        }

        onDone(success ? 'Login successful' : 'Login interrupted')
      }}
    />
  )
}

export function Login(props: {
  onDone: (success: boolean, mainLoopModel: string) => void
  startingMessage?: string
}): React.ReactNode {
  const mainLoopModel = useMainLoopModel()
  const configuredAuthProvider = getConfiguredAuthProvider()
  const [selectedProvider, setSelectedProvider] =
    useState<AuthProviderChoice | null>(null)

  const providerOptions = useMemo(
    () => [
      {
        label: (
          <Text>
            Anthropic{' '}
            <Text dimColor={true}>
              Subscription login, Console API billing, or Bedrock/Foundry/Vertex
            </Text>
            {'\n'}
          </Text>
        ),
        value: 'anthropic',
      },
      {
        label: (
          <Text>
            OpenAI / Codex{' '}
            <Text dimColor={true}>
              Codex login, Codex auth import, or OpenAI API key
            </Text>
            {'\n'}
          </Text>
        ),
        value: 'openai',
      },
      {
        label: (
          <Text>
            OpenRouter{' '}
            <Text dimColor={true}>OpenRouter API key via Responses API</Text>
            {'\n'}
          </Text>
        ),
        value: 'openrouter',
      },
      {
        label: (
          <Text>
            FirePass{' '}
            <Text dimColor={true}>
              Fireworks API key with Kimi K2.5 Turbo subscription
            </Text>
            {'\n'}
          </Text>
        ),
        value: 'firepass',
      },
    ],
    [],
  )

  const onCancel = () => props.onDone(false, mainLoopModel)
  const onFlowDone = () => props.onDone(true, mainLoopModel)

  const body =
    selectedProvider === null ? (
      <Box flexDirection="column" gap={1}>
        <Text bold={true}>
          {props.startingMessage ??
            'Choose which provider you want Oroboros-Anthropic Claude CLI to use.'}
        </Text>
        <Text dimColor={true}>
          Current default: {configuredAuthProvider}. Pick a provider first, then
          choose the login method inside that flow.
        </Text>
        <Text>Select provider:</Text>
        <Box>
          <Select
            options={providerOptions}
            onChange={value =>
              setSelectedProvider(value as AuthProviderChoice)
            }
          />
        </Box>
      </Box>
    ) : selectedProvider === 'openai' ? (
      <OpenAILoginFlow
        onDone={onFlowDone}
        startingMessage="Oroboros-Anthropic Claude CLI can use OpenAI with your Codex/ChatGPT login or a standard OpenAI API key."
      />
    ) : selectedProvider === 'openrouter' ? (
      <OpenRouterLoginFlow
        onDone={onFlowDone}
        startingMessage="Oroboros-Anthropic Claude CLI can use OpenRouter with your OpenRouter API key."
      />
    ) : selectedProvider === 'firepass' ? (
      <FirepassLoginFlow
        onDone={onFlowDone}
        startingMessage="Oroboros-Anthropic Claude CLI can use FirePass with your Fireworks API key for Kimi K2.5 Turbo."
      />
    ) : (
      <ConsoleOAuthFlow
        onDone={onFlowDone}
        startingMessage="Oroboros-Anthropic Claude CLI can use Anthropic login, Anthropic Console billing, or Anthropic-compatible 3rd-party platforms."
      />
    )

  return (
    <Dialog
      title="Login"
      onCancel={onCancel}
      color="permission"
      inputGuide={exitState =>
        exitState.pending ? (
          <Text>Press {exitState.keyName} again to exit</Text>
        ) : (
          <ConfigurableShortcutHint
            action="confirm:no"
            context="Confirmation"
            fallback="Esc"
            description="cancel"
          />
        )
      }
    >
      {body}
    </Dialog>
  )
}
