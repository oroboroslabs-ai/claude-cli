import { readFileSync } from 'fs'

const pkg = JSON.parse(readFileSync('./package.json', 'utf-8'))
const version = pkg.version

const result = await Bun.build({
  entrypoints: ['./src/entrypoints/cli.tsx'],
  outdir: './dist',
  target: 'node',
  format: 'esm',
  splitting: false,
  sourcemap: 'external',
  minify: false,
  naming: 'cli.mjs',
  define: {
    'MACRO.VERSION': JSON.stringify(version),
    'MACRO.DISPLAY_VERSION': JSON.stringify(version),
    'MACRO.BUILD_TIME': JSON.stringify(new Date().toISOString()),
    'MACRO.ISSUES_EXPLAINER': JSON.stringify(
      'report the issue at https://github.com/oroboroslabs-ai/claude-cli/issues',
    ),
  },
  plugins: [
    {
      name: 'claude-cli-build-shim',
      setup(build) {
        const internalFeatureStubModules = new Map([
          [
            '../daemon/workerRegistry.js',
            'export async function runDaemonWorker() { throw new Error("Daemon worker is unavailable in this Oroboros-Anthropic Claude CLI build."); }',
          ],
          [
            '../daemon/main.js',
            'export async function daemonMain() { throw new Error("Daemon mode is unavailable in this Oroboros-Anthropic Claude CLI build."); }',
          ],
          [
            '../cli/bg.js',
            `
export async function psHandler() { throw new Error("Background sessions are unavailable in this Oroboros-Anthropic Claude CLI build."); }
export async function logsHandler() { throw new Error("Background sessions are unavailable in this Oroboros-Anthropic Claude CLI build."); }
export async function attachHandler() { throw new Error("Background sessions are unavailable in this Oroboros-Anthropic Claude CLI build."); }
export async function killHandler() { throw new Error("Background sessions are unavailable in this Oroboros-Anthropic Claude CLI build."); }
export async function handleBgFlag() { throw new Error("Background sessions are unavailable in this Oroboros-Anthropic Claude CLI build."); }
`,
          ],
          [
            '../cli/handlers/templateJobs.js',
            'export async function templatesMain() { throw new Error("Template jobs are unavailable in this Oroboros-Anthropic Claude CLI build."); }',
          ],
          [
            '../environment-runner/main.js',
            'export async function environmentRunnerMain() { throw new Error("Environment runner is unavailable in this Oroboros-Anthropic Claude CLI build."); }',
          ],
          [
            '../self-hosted-runner/main.js',
            'export async function selfHostedRunnerMain() { throw new Error("Self-hosted runner is unavailable in this Oroboros-Anthropic Claude CLI build."); }',
          ],
          [
            './components/agents/SnapshotUpdateDialog.js',
            'export function SnapshotUpdateDialog() { return null; }',
          ],
          [
            './assistant/AssistantSessionChooser.js',
            'export function AssistantSessionChooser() { return null; }',
          ],
          [
            './commands/assistant/assistant.js',
            "export function NewInstallWizard() { return null; } export async function computeDefaultInstallDir() { return '.claude-cli-assistant'; }",
          ],
          [
            './commands/agents-platform/index.js',
            'export default async function agentsPlatformCommand() { throw new Error("Agents platform is unavailable in this Oroboros-Anthropic Claude CLI build."); }',
          ],
          [
            './tools/TungstenTool/TungstenTool.js',
            "export const TungstenTool = { name: 'TungstenTool' };",
          ],
          [
            '../tools/TungstenTool/TungstenTool.js',
            "export const TungstenTool = { name: 'TungstenTool' };",
          ],
          [
            '../../tools/TungstenTool/TungstenTool.js',
            "export const TungstenTool = { name: 'TungstenTool' };",
          ],
          [
            '../tools/TungstenTool/TungstenLiveMonitor.js',
            'export function TungstenLiveMonitor() { return null; }',
          ],
          [
            './tools/REPLTool/REPLTool.js',
            "export const REPLTool = { name: 'REPLTool' };",
          ],
          [
            './tools/SuggestBackgroundPRTool/SuggestBackgroundPRTool.js',
            "export const SuggestBackgroundPRTool = { name: 'SuggestBackgroundPRTool' };",
          ],
          [
            './tools/VerifyPlanExecutionTool/VerifyPlanExecutionTool.js',
            "export const VerifyPlanExecutionTool = { name: 'VerifyPlanExecutionTool' };",
          ],
        ] as const)

        build.onResolve({ filter: /^bun:bundle$/ }, () => ({
          path: 'bun:bundle',
          namespace: 'bun-bundle-shim',
        }))
        build.onLoad(
          { filter: /.*/, namespace: 'bun-bundle-shim' },
          () => ({
            contents: `export function feature() { return false; }`,
            loader: 'js',
          }),
        )

        build.onResolve(
          {
            filter:
              /^(\.\.\/(daemon\/workerRegistry|daemon\/main|cli\/bg|cli\/handlers\/templateJobs|environment-runner\/main|self-hosted-runner\/main)|\.\/(components\/agents\/SnapshotUpdateDialog|assistant\/AssistantSessionChooser|commands\/assistant\/assistant|commands\/agents-platform\/index|tools\/REPLTool\/REPLTool|tools\/SuggestBackgroundPRTool\/SuggestBackgroundPRTool|tools\/VerifyPlanExecutionTool\/VerifyPlanExecutionTool|tools\/TungstenTool\/TungstenTool)|\.\.\/tools\/TungstenTool\/Tungsten(LiveMonitor|Tool)|\.\.\/\.\.\/tools\/TungstenTool\/TungstenTool)\.js$/,
          },
          args => {
            if (!internalFeatureStubModules.has(args.path)) return null
            return {
              path: args.path,
              namespace: 'internal-feature-stub',
            }
          },
        )
        build.onLoad(
          { filter: /.*/, namespace: 'internal-feature-stub' },
          args => ({
            contents: internalFeatureStubModules.get(args.path) ?? 'export {}',
            loader: 'js',
          }),
        )

        build.onResolve({ filter: /^react\/compiler-runtime$/ }, () => ({
          path: 'react/compiler-runtime',
          namespace: 'react-compiler-shim',
        }))
        build.onLoad(
          { filter: /.*/, namespace: 'react-compiler-shim' },
          () => ({
            contents:
              "export function c(size) { return new Array(size).fill(Symbol.for('react.memo_cache_sentinel')); }",
            loader: 'js',
          }),
        )

        for (const mod of [
          'audio-capture-napi',
          'audio-capture.node',
          'image-processor-napi',
          'modifiers-napi',
          'url-handler-napi',
          'color-diff-napi',
          'sharp',
          '@anthropic-ai/mcpb',
          '@ant/claude-for-chrome-mcp',
          '@ant/computer-use-mcp',
          '@anthropic-ai/sandbox-runtime',
          'asciichart',
          'plist',
          'cacache',
          'fuse',
          'code-excerpt',
          'stack-utils',
        ]) {
          build.onResolve({ filter: new RegExp(`^${mod}$`) }, () => ({
            path: mod,
            namespace: 'native-stub',
          }))
        }
        build.onLoad(
          { filter: /.*/, namespace: 'native-stub' },
          () => ({
            contents: `
const noop = () => null;
const noopClass = class {};
const handler = {
  get(_, prop) {
    if (prop === '__esModule') return true;
    if (prop === 'default') return new Proxy({}, handler);
    if (prop === 'ExportResultCode') return { SUCCESS: 0, FAILED: 1 };
    if (prop === 'resourceFromAttributes') return () => ({});
    if (prop === 'SandboxRuntimeConfigSchema') return { parse: () => ({}) };
    return noop;
  }
};
const stub = new Proxy(noop, handler);
export default stub;
export const __stub = true;
export const SandboxViolationStore = null;
export const SandboxManager = new Proxy({}, { get: () => noop });
export const SandboxRuntimeConfigSchema = { parse: () => ({}) };
export const BROWSER_TOOLS = [];
export const getMcpConfigForManifest = noop;
export const ColorDiff = null;
export const ColorFile = null;
export const getSyntaxTheme = noop;
export const plot = noop;
export const createClaudeForChromeMcpServer = noop;
export const createComputerUseMcpServer = noop;
export const ExportResultCode = { SUCCESS: 0, FAILED: 1 };
export const resourceFromAttributes = noop;
export const Resource = noopClass;
export const SimpleSpanProcessor = noopClass;
export const BatchSpanProcessor = noopClass;
export const NodeTracerProvider = noopClass;
export const BasicTracerProvider = noopClass;
export const OTLPTraceExporter = noopClass;
export const OTLPLogExporter = noopClass;
export const OTLPMetricExporter = noopClass;
export const PrometheusExporter = noopClass;
export const LoggerProvider = noopClass;
export const SimpleLogRecordProcessor = noopClass;
export const BatchLogRecordProcessor = noopClass;
export const MeterProvider = noopClass;
export const PeriodicExportingMetricReader = noopClass;
export const trace = { getTracer: () => ({ startSpan: () => ({ end: noop, setAttribute: noop, setStatus: noop, recordException: noop }) }) };
export const context = { active: noop, with: (_, fn) => fn() };
export const SpanStatusCode = { OK: 0, ERROR: 1, UNSET: 2 };
export const ATTR_SERVICE_NAME = 'service.name';
export const ATTR_SERVICE_VERSION = 'service.version';
export const SEMRESATTRS_SERVICE_NAME = 'service.name';
export const SEMRESATTRS_SERVICE_VERSION = 'service.version';
export const AggregationTemporality = { CUMULATIVE: 0, DELTA: 1 };
export const DataPointType = { HISTOGRAM: 0, SUM: 1, GAUGE: 2 };
export const InstrumentType = { COUNTER: 0, HISTOGRAM: 1, UP_DOWN_COUNTER: 2 };
export const PushMetricExporter = noopClass;
export const SeverityNumber = {};
`,
            loader: 'js',
          }),
        )

        build.onResolve(
          { filter: /\.(md|txt)$/ },
          args => ({
            path: args.path,
            namespace: 'text-stub',
          }),
        )
        build.onLoad(
          { filter: /.*/, namespace: 'text-stub' },
          () => ({
            contents: `export default '';`,
            loader: 'js',
          }),
        )
      },
    },
  ],
  external: [
    '@opentelemetry/api',
    '@opentelemetry/api-logs',
    '@opentelemetry/core',
    '@opentelemetry/exporter-trace-otlp-grpc',
    '@opentelemetry/exporter-trace-otlp-http',
    '@opentelemetry/exporter-trace-otlp-proto',
    '@opentelemetry/exporter-logs-otlp-http',
    '@opentelemetry/exporter-logs-otlp-proto',
    '@opentelemetry/exporter-logs-otlp-grpc',
    '@opentelemetry/exporter-metrics-otlp-proto',
    '@opentelemetry/exporter-metrics-otlp-grpc',
    '@opentelemetry/exporter-metrics-otlp-http',
    '@opentelemetry/exporter-prometheus',
    '@opentelemetry/resources',
    '@opentelemetry/sdk-trace-base',
    '@opentelemetry/sdk-trace-node',
    '@opentelemetry/sdk-logs',
    '@opentelemetry/sdk-metrics',
    '@opentelemetry/semantic-conventions',
    '@aws-sdk/client-bedrock',
    '@aws-sdk/client-bedrock-runtime',
    '@aws-sdk/client-sts',
    '@aws-sdk/credential-providers',
    '@azure/identity',
    'google-auth-library',
  ],
})

if (!result.success) {
  console.error('Build failed:')
  for (const log of result.logs) {
    console.error(log)
  }
  process.exit(1)
}

console.log(`Built Oroboros-Anthropic Claude CLI v${version} -> dist/cli.mjs`)
