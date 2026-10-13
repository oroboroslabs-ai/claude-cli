import { spawn } from 'child_process'
import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  statSync,
  writeFileSync,
} from 'fs'
import { join, resolve } from 'path'

type Mode = 'startup' | 'query'

type RunSummary = {
  mode: Mode
  command: string[]
  artifactDir: string
  startupReportPath: string | null
  queryReportPath: string | null
  wallTimeMs: number
  exitCode: number
  startupTotalMs: number | null
  queryTtftMs: number | null
  queryTotalTimeMs: number | null
  queryPreApiOverheadMs: number | null
}

function fail(message: string): never {
  process.stderr.write(`${message}\n`)
  process.exit(1)
}

function parseArgs(argv: string[]): { mode: Mode; cliArgs: string[] } {
  const [mode, ...rest] = argv
  if (mode !== 'startup' && mode !== 'query') {
    fail(
      'Usage: bun run scripts/perf.ts <startup|query> -- <claude-cli args...>',
    )
  }

  const separatorIdx = rest.indexOf('--')
  const cliArgs = separatorIdx === -1 ? rest : rest.slice(separatorIdx + 1)
  return { mode, cliArgs }
}

function ensureBuilt(): void {
  if (!existsSync(resolve('dist/cli.mjs'))) {
    fail('Missing dist/cli.mjs. Run `bun run build` before running perf scripts.')
  }
}

function getRunId(): string {
  return new Date().toISOString().replace(/[:.]/g, '-')
}

function getLatestFile(dir: string): string | null {
  if (!existsSync(dir)) return null
  const files = readdirSync(dir)
    .map(name => join(dir, name))
    .filter(path => statSync(path).isFile())
    .sort(
      (a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs,
    )
  return files[0] ?? null
}

function extractMs(report: string, regex: RegExp): number | null {
  const match = report.match(regex)
  if (!match?.[1]) return null
  const value = Number.parseFloat(match[1])
  return Number.isFinite(value) ? value : null
}

function readMaybe(path: string | null): string | null {
  if (!path) return null
  return readFileSync(path, 'utf8')
}

async function runCommand(
  mode: Mode,
  cliArgs: string[],
  artifactDir: string,
): Promise<RunSummary> {
  const configDir = join(artifactDir, 'config')
  const debugDir = join(artifactDir, 'debug')
  mkdirSync(configDir, { recursive: true })
  mkdirSync(debugDir, { recursive: true })

  const childArgs = ['dist/cli.mjs', ...cliArgs]
  if (
    mode === 'query' &&
    !cliArgs.some(
      arg => arg === '--debug-file' || arg.startsWith('--debug-file='),
    )
  ) {
    childArgs.splice(1, 0, '--debug-file', join(debugDir, 'query-debug.txt'))
  }

  const env = {
    ...process.env,
    CLAUDE_CLI_CONFIG_DIR: configDir,
    CLAUDE_CODE_DEBUG_LOGS_DIR: debugDir,
    CLAUDE_CODE_PROFILE_STARTUP: mode === 'startup' ? '1' : '0',
    CLAUDE_CODE_PROFILE_QUERY: mode === 'query' ? '1' : '0',
  }

  const startedAt = Date.now()
  const exitCode = await new Promise<number>((resolveExit, reject) => {
    const child = spawn('node', childArgs, {
      cwd: resolve('.'),
      env,
      stdio: 'inherit',
    })

    child.on('error', reject)
    child.on('exit', code => resolveExit(code ?? 1))
  })
  const wallTimeMs = Date.now() - startedAt

  const startupReportPath = getLatestFile(join(configDir, 'startup-perf'))
  const queryReportPath = getLatestFile(join(configDir, 'query-perf'))
  const startupReport = readMaybe(startupReportPath)
  const queryReport = readMaybe(queryReportPath)

  return {
    mode,
    command: ['node', ...childArgs],
    artifactDir,
    startupReportPath,
    queryReportPath,
    wallTimeMs,
    exitCode,
    startupTotalMs: startupReport
      ? extractMs(startupReport, /Total startup time:\s+([0-9.]+)ms/)
      : null,
    queryTtftMs: queryReport
      ? extractMs(queryReport, /Total TTFT:\s+([0-9.]+)ms/)
      : null,
    queryTotalTimeMs: queryReport
      ? extractMs(queryReport, /Total time:\s+([0-9.]+)ms/)
      : null,
    queryPreApiOverheadMs: queryReport
      ? extractMs(queryReport, /Total pre-API overhead\s+([0-9.]+)ms/)
      : null,
  }
}

const { mode, cliArgs } = parseArgs(process.argv.slice(2))
ensureBuilt()

const artifactDir = resolve('.perf-artifacts', `${mode}-${getRunId()}`)
mkdirSync(artifactDir, { recursive: true })

const summary = await runCommand(mode, cliArgs, artifactDir)
const summaryPath = join(artifactDir, 'summary.json')
writeFileSync(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, 'utf8')

process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`)
process.stdout.write(`Summary written to ${summaryPath}\n`)

if (summary.exitCode !== 0) {
  process.exit(summary.exitCode)
}
