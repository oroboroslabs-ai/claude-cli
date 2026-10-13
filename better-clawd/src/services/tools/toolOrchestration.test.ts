import { afterEach, expect, test } from 'bun:test'
import {
  DEFAULT_MAX_TOOL_USE_CONCURRENCY,
  getMaxToolUseConcurrency,
} from './toolConcurrency.js'

const ORIGINAL_CONCURRENCY = process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY

afterEach(() => {
  if (ORIGINAL_CONCURRENCY === undefined) {
    delete process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY
  } else {
    process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY = ORIGINAL_CONCURRENCY
  }
})

test('defaults tool concurrency to a bounded budget', () => {
  delete process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY
  expect(getMaxToolUseConcurrency()).toBe(DEFAULT_MAX_TOOL_USE_CONCURRENCY)
})

test('allows an explicit positive concurrency override', () => {
  process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY = '7'
  expect(getMaxToolUseConcurrency()).toBe(7)
})

test('ignores invalid concurrency overrides', () => {
  process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY = '0'
  expect(getMaxToolUseConcurrency()).toBe(DEFAULT_MAX_TOOL_USE_CONCURRENCY)

  process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY = 'not-a-number'
  expect(getMaxToolUseConcurrency()).toBe(DEFAULT_MAX_TOOL_USE_CONCURRENCY)
})
