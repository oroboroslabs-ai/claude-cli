import { expect, test } from 'bun:test'
import { getNextTaskOutputPollIntervalMs } from './taskOutputPolling.js'

test('resets task output polling to the active interval on new activity', () => {
  expect(getNextTaskOutputPollIntervalMs(4000, true)).toBe(250)
})

test('backs task output polling off when the command is quiet', () => {
  let intervalMs = getNextTaskOutputPollIntervalMs(250, false)
  expect(intervalMs).toBe(1000)

  intervalMs = getNextTaskOutputPollIntervalMs(intervalMs, false)
  expect(intervalMs).toBe(2000)

  intervalMs = getNextTaskOutputPollIntervalMs(intervalMs, false)
  expect(intervalMs).toBe(4000)

  expect(getNextTaskOutputPollIntervalMs(intervalMs, false)).toBe(4000)
})
