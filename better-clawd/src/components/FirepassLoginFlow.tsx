import * as React from 'react'
import { useState } from 'react'
import { Box, Text } from '../ink.js'
import { saveFirepassApiKey } from '../utils/auth.js'
import { Spinner } from './Spinner.js'
import TextInput from './TextInput.js'

type FirepassLoginFlowProps = {
  onDone: () => void
  startingMessage?: string
}

export function FirepassLoginFlow({
  onDone,
  startingMessage,
}: FirepassLoginFlowProps): React.ReactNode {
  const [isBusy, setIsBusy] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [cursorOffset, setCursorOffset] = useState(0)

  async function handleSubmit(value: string): Promise<void> {
    const trimmed = value.trim()
    if (!trimmed) {
      return
    }

    setIsBusy(true)
    setStatus(null)
    try {
      await saveFirepassApiKey(trimmed)
      onDone()
    } catch (error) {
      setStatus(error instanceof Error ? error.message : String(error))
    } finally {
      setIsBusy(false)
    }
  }

  if (isBusy) {
    return (
      <Box flexDirection="column" gap={1}>
        <Box>
          <Spinner />
          <Text>Configuring FirePass login for Oroboros-Anthropic Claude CLI...</Text>
        </Box>
        <Text dimColor={true}>
          FirePass uses your Fireworks API key with the Anthropic-compatible
          endpoint at `https://api.fireworks.ai/inference`.
        </Text>
      </Box>
    )
  }

  return (
    <Box flexDirection="column" gap={1}>
      <Text>
        {startingMessage ??
          'Oroboros-Anthropic Claude CLI can use FirePass with your Fireworks API key.'}
      </Text>
      <Text dimColor={true}>
        FirePass provides subscription-based access to Kimi K2.5 Turbo with no
        per-token charges. Get FirePass at{' '}
        <Text color="cyan">https://app.fireworks.ai/fire-pass</Text>
      </Text>
      <Box>
        <Text>Paste your Fireworks API key:</Text>
        <TextInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          onExit={() => {
            setInputValue('')
            setCursorOffset(0)
          }}
          cursorOffset={cursorOffset}
          onChangeCursorOffset={setCursorOffset}
          columns={72}
          mask="*"
        />
      </Box>
      {status ? <Text color="error">{status}</Text> : null}
      <Text dimColor={true}>
        Press <Text bold={true}>Enter</Text> to save, or <Text bold={true}>Esc</Text>{' '}
        to cancel.
      </Text>
    </Box>
  )
}