type AnthropicTool = {
  name: string
  description?: string
  input_schema?: Record<string, unknown>
}

type AnthropicContentBlock =
  | { type: 'text'; text: string }
  | { type: 'tool_use'; id?: string; name: string; input?: unknown }
  | { type: 'tool_result'; tool_use_id?: string; content?: unknown }
  | { type: string; [key: string]: unknown }

type AnthropicMessage = {
  role: 'user' | 'assistant'
  content: string | AnthropicContentBlock[]
}

type AnthropicMessagesCreateParams = {
  model: string
  messages: AnthropicMessage[]
  system?: string | Array<{ type?: string; text?: string }>
  tools?: AnthropicTool[]
  tool_choice?: { type?: string; name?: string } | null
  max_tokens?: number
  temperature?: number
  stream?: boolean
}

type OpenAIResponseOutputItem =
  | {
      type: 'message'
      role?: 'assistant'
      content?: Array<{ type: string; text?: string }>
    }
  | {
      type: 'function_call'
      id?: string
      call_id?: string
      name: string
      arguments?: string
    }
  | {
      type: string
      id?: string
      call_id?: string
      name?: string
      arguments?: string
      content?: Array<{ type: string; text?: string }>
      summary?: Array<{ type: string; text?: string }>
    }

type OpenAIResponse = {
  id: string
  model: string
  output?: OpenAIResponseOutputItem[]
  usage?: {
    input_tokens?: number
    output_tokens?: number
    total_tokens?: number
  }
}

type OpenAICompatOptions = {
  apiKey: string
  baseURL: string
  defaultHeaders?: Record<string, string>
  fetchImpl?: typeof fetch
  timeoutMs: number
}

type StreamWithResponse = {
  withResponse(): Promise<{
    request_id: string
    response: Response
    data: OpenAICompatStream
  }>
}

class OpenAICompatStream implements AsyncIterable<Record<string, unknown>> {
  private readonly events: Record<string, unknown>[]
  controller = {
    abort: () => {
      this.aborted = true
    },
  }
  private aborted = false

  constructor(events: Record<string, unknown>[]) {
    this.events = events
  }

  async *[Symbol.asyncIterator](): AsyncIterator<Record<string, unknown>> {
    for (const event of this.events) {
      if (this.aborted) {
        return
      }
      yield event
    }
  }
}

function normalizeOpenAIModel(model: string): string {
  if (
    model.startsWith('gpt-') ||
    model.startsWith('o') ||
    model.startsWith('codex')
  ) {
    return model
  }
  return process.env.OPENAI_DEFAULT_MODEL || 'gpt-5.4'
}

function systemToInstructions(
  system?: AnthropicMessagesCreateParams['system'],
): string | undefined {
  if (!system) {
    return undefined
  }
  if (typeof system === 'string') {
    return system
  }
  return system
    .map(block => ('text' in block && typeof block.text === 'string' ? block.text : ''))
    .filter(Boolean)
    .join('\n\n')
}

function stringifyToolOutput(content: unknown): string {
  if (typeof content === 'string') {
    return content
  }
  if (Array.isArray(content)) {
    return content
      .map(item => {
        if (typeof item === 'string') {
          return item
        }
        if (
          item &&
          typeof item === 'object' &&
          'text' in item &&
          typeof item.text === 'string'
        ) {
          return item.text
        }
        return JSON.stringify(item)
      })
      .join('\n')
  }
  return JSON.stringify(content ?? '')
}

function anthropicMessagesToOpenAIInput(
  messages: AnthropicMessage[],
): Array<Record<string, unknown>> {
  const input: Array<Record<string, unknown>> = []

  for (const message of messages) {
    if (typeof message.content === 'string') {
      input.push({ role: message.role, content: message.content })
      continue
    }

    let bufferedText: string[] = []
    const flushBufferedText = () => {
      if (bufferedText.length === 0) {
        return
      }
      input.push({
        role: message.role,
        content: bufferedText.join('\n'),
      })
      bufferedText = []
    }

    for (const block of message.content) {
      if (block.type === 'text' && typeof block.text === 'string') {
        bufferedText.push(block.text)
        continue
      }

      flushBufferedText()

      if (block.type === 'tool_use' && message.role === 'assistant') {
        input.push({
          type: 'function_call',
          call_id: block.id ?? `call_${block.name}`,
          name: block.name,
          arguments: JSON.stringify(block.input ?? {}),
        })
        continue
      }

      if (block.type === 'tool_result' && message.role === 'user') {
        input.push({
          type: 'function_call_output',
          call_id: block.tool_use_id ?? 'tool_call',
          output: stringifyToolOutput(block.content),
        })
        continue
      }

      input.push({
        role: message.role,
        content: `[${block.type}] ${stringifyToolOutput(block)}`,
      })
    }

    flushBufferedText()
  }

  return input
}

function anthropicToolsToOpenAI(
  tools?: AnthropicTool[],
): Array<Record<string, unknown>> | undefined {
  if (!tools || tools.length === 0) {
    return undefined
  }

  return tools.map(tool => ({
    type: 'function',
    name: tool.name,
    description: tool.description,
    parameters: tool.input_schema ?? {
      type: 'object',
      properties: {},
      additionalProperties: true,
    },
    strict: false,
  }))
}

function anthropicToolChoiceToOpenAI(
  toolChoice: AnthropicMessagesCreateParams['tool_choice'],
): string | Record<string, unknown> | undefined {
  if (!toolChoice?.type) {
    return undefined
  }
  if (toolChoice.type === 'auto' || toolChoice.type === 'none') {
    return toolChoice.type
  }
  if (toolChoice.type === 'tool' && toolChoice.name) {
    return {
      type: 'function',
      name: toolChoice.name,
    }
  }
  return undefined
}

function extractAssistantText(item: OpenAIResponseOutputItem): string {
  if ('content' in item && Array.isArray(item.content)) {
    return item.content
      .map(part => (typeof part.text === 'string' ? part.text : ''))
      .join('')
  }
  if ('summary' in item && Array.isArray(item.summary)) {
    return item.summary
      .map(part => (typeof part.text === 'string' ? part.text : ''))
      .join('')
  }
  return ''
}

function openAIOutputToAnthropicBlocks(
  output: OpenAIResponseOutputItem[] = [],
): Array<Record<string, unknown>> {
  const blocks: Array<Record<string, unknown>> = []

  for (const item of output) {
    if (item.type === 'message') {
      const text = extractAssistantText(item)
      if (text) {
        blocks.push({ type: 'text', text })
      }
      continue
    }

    if (item.type === 'function_call') {
      let parsedArguments: unknown = {}
      try {
        parsedArguments = item.arguments ? JSON.parse(item.arguments) : {}
      } catch {
        parsedArguments = item.arguments ?? {}
      }
      blocks.push({
        type: 'tool_use',
        id: item.call_id ?? item.id ?? `call_${item.name}`,
        name: item.name,
        input: parsedArguments,
      })
      continue
    }

    const text = extractAssistantText(item)
    if (text) {
      blocks.push({ type: 'text', text })
    }
  }

  return blocks
}

function openAIResponseToAnthropicMessage(
  response: OpenAIResponse,
  model: string,
): Record<string, unknown> {
  const blocks = openAIOutputToAnthropicBlocks(response.output)
  const stopReason = blocks.some(block => block.type === 'tool_use')
    ? 'tool_use'
    : 'end_turn'

  return {
    id: response.id,
    type: 'message',
    role: 'assistant',
    model,
    content: blocks,
    stop_reason: stopReason,
    stop_sequence: null,
    usage: {
      input_tokens: response.usage?.input_tokens ?? 0,
      output_tokens: response.usage?.output_tokens ?? 0,
    },
  }
}

function openAIResponseToAnthropicEvents(
  response: OpenAIResponse,
  model: string,
): Record<string, unknown>[] {
  const message = openAIResponseToAnthropicMessage(response, model)
  const blocks = (message.content as Array<Record<string, unknown>>) ?? []
  const events: Record<string, unknown>[] = [
    {
      type: 'message_start',
      message,
    },
  ]

  blocks.forEach((block, index) => {
    if (block.type === 'text') {
      events.push({
        type: 'content_block_start',
        index,
        content_block: { type: 'text', text: '' },
      })
      events.push({
        type: 'content_block_delta',
        index,
        delta: {
          type: 'text_delta',
          text: block.text,
        },
      })
      events.push({ type: 'content_block_stop', index })
      return
    }

    if (block.type === 'tool_use') {
      const rawInput =
        typeof block.input === 'string'
          ? block.input
          : JSON.stringify(block.input ?? {})
      events.push({
        type: 'content_block_start',
        index,
        content_block: {
          type: 'tool_use',
          id: block.id,
          name: block.name,
          input: '',
        },
      })
      events.push({
        type: 'content_block_delta',
        index,
        delta: {
          type: 'input_json_delta',
          partial_json: rawInput,
        },
      })
      events.push({ type: 'content_block_stop', index })
    }
  })

  events.push({
    type: 'message_delta',
    delta: {
      stop_reason: message.stop_reason,
      stop_sequence: null,
    },
    usage: {
      output_tokens: response.usage?.output_tokens ?? 0,
    },
  })
  events.push({ type: 'message_stop' })
  return events
}

function buildOpenAIRequestBody(
  params: AnthropicMessagesCreateParams,
): Record<string, unknown> {
  return {
    model: normalizeOpenAIModel(params.model),
    input: anthropicMessagesToOpenAIInput(params.messages),
    instructions: systemToInstructions(params.system),
    tools: anthropicToolsToOpenAI(params.tools),
    tool_choice: anthropicToolChoiceToOpenAI(params.tool_choice),
    max_output_tokens: params.max_tokens,
    temperature: params.temperature,
  }
}

export class OpenAIResponsesCompatClient {
  private readonly options: OpenAICompatOptions

  beta = {
    messages: {
      create: (
        params: AnthropicMessagesCreateParams,
        requestOptions?: { signal?: AbortSignal },
      ): Promise<Record<string, unknown>> | StreamWithResponse => {
        if (params.stream) {
          return {
            withResponse: async () => {
              const response = await this.createResponse(params, requestOptions)
              const stream = new OpenAICompatStream(
                openAIResponseToAnthropicEvents(
                  response,
                  normalizeOpenAIModel(params.model),
                ),
              )
              return {
                request_id: response.id,
                response: new Response(JSON.stringify(response), {
                  status: 200,
                  headers: { 'content-type': 'application/json' },
                }),
                data: stream,
              }
            },
          }
        }
        return this.createResponse(params, requestOptions).then(response =>
          openAIResponseToAnthropicMessage(
            response,
            normalizeOpenAIModel(params.model),
          ),
        )
      },
    },
  }

  constructor(options: OpenAICompatOptions) {
    this.options = options
  }

  private async createResponse(
    params: AnthropicMessagesCreateParams,
    requestOptions?: { signal?: AbortSignal },
  ): Promise<OpenAIResponse> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), this.options.timeoutMs)
    requestOptions?.signal?.addEventListener('abort', () => controller.abort())

    try {
      const response = await (this.options.fetchImpl ?? globalThis.fetch)(
        `${this.options.baseURL.replace(/\/$/, '')}/responses`,
        {
          method: 'POST',
          signal: controller.signal,
          headers: {
            'content-type': 'application/json',
            Authorization: `Bearer ${this.options.apiKey}`,
            ...this.options.defaultHeaders,
          },
          body: JSON.stringify(buildOpenAIRequestBody(params)),
        },
      )

      if (!response.ok) {
        throw new Error(
          `OpenAI Responses API error ${response.status}: ${await response.text()}`,
        )
      }

      return (await response.json()) as OpenAIResponse
    } finally {
      clearTimeout(timeout)
    }
  }
}
