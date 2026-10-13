# Performance Workflow

This repository includes a lightweight performance workflow built around the
existing startup and query profilers.

## Build Once

```bash
bun run build
```

## Baseline Scenarios

1. Cold start and command latency

```bash
bun run perf:startup -- --help
```

2. Interactive startup in a real session

```bash
bun run perf:startup --
```

Use your OS task manager while the app is idle to inspect CPU, RSS, and handle
count after first render.

3. Headless query / TTFT

```bash
bun run perf:query -- --print "Summarize the current directory."
```

This requires whatever auth/config is normally needed for the chosen provider.

## Artifacts

Each run writes an isolated artifact bundle under `.perf-artifacts/`:

- `summary.json`: wall-clock timing and parsed profiler highlights
- `config/startup-perf/*`: startup profiler output
- `config/query-perf/*`: query profiler output
- `debug/*`: debug logs for runs that need them

## Regression Checks

Run the focused regression checks for the new performance helpers with:

```bash
bun run perf:regression
```

## Suggested Before/After Loop

1. Run the startup baseline.
2. Run the headless query baseline.
3. If you are changing long-running behavior, also launch an interactive session and
   watch idle CPU and memory for a few minutes.
4. Compare the new `.perf-artifacts` summary against the previous run before and
   after each optimization pass.
