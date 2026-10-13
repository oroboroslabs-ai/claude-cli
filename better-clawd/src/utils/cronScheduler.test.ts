import { expect, test } from 'bun:test'
import { getSchedulerCheckDelayMs } from './cronScheduler.js'

test('uses a slower idle cadence when no cron tasks are pending', () => {
  expect(getSchedulerCheckDelayMs(null, 10_000)).toBe(2000)
})

test('keeps the minimum cadence for tasks that are due soon', () => {
  expect(getSchedulerCheckDelayMs(10_500, 10_000)).toBe(1000)
})

test('backs off proportionally for tasks scheduled farther out', () => {
  expect(getSchedulerCheckDelayMs(16_000, 10_000)).toBe(3000)
  expect(getSchedulerCheckDelayMs(22_000, 10_000)).toBe(5000)
})
