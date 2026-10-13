# Oroboros-Anthropic Claude CLI

> Claude Code, but better.

Oroboros-Anthropic Claude CLI exists because the original had a genuinely great core idea and too many self-inflicted problems around it. This fork keeps what worked, fixes what did not, and gives people real choice over how they log in, which provider they use, and how much of the product they actually want phoning home.

No telemetry. No vendor lock-in. Faster startup, lower idle overhead, and better long-session performance than the original Claude Code. Less corporate baggage.

[NPM package](https://www.npmjs.com/package/claude-cli) 

## Install

```bash
npm install -g claude-cli
```

Or run it without a global install:

```bash
npx claude-cli
```

## Why This Exists

Claude Code had the bones of a best-in-class coding CLI, but too much of the experience was tied to one company, one backend, one set of assumptions, and one way of doing things.

Oroboros-Anthropic Claude CLI is the response to that.

- It keeps the good parts of the original UX
- It removes telemetry and unnecessary phone-home behavior
- It supports multiple providers without turning setup into a science project
- It improves performance over the original Claude Code, with better startup behavior, less idle background churn, and smoother long sessions
- It is easier to inspect, modify, and run on your own terms

## Performance

Oroboros-Anthropic Claude CLI is intentionally tuned to be leaner than upstream Claude Code:

- Lower startup and initialization cost
- Less background polling and idle CPU churn
- Better memory and render behavior during long transcript-heavy sessions
- Focused performance workflow and regression checks in `PERFORMANCE.md`

## What Oroboros-Anthropic Claude CLI Changes

- Full Oroboros-Anthropic Claude CLI rebrand across the CLI, UI, config paths, installers, and app identity
- OpenAI support with API keys and Codex-based login import/refresh flow
- OpenRouter support with proper provider wiring
- Anthropic support kept for people who still want it
- Telemetry stripped out
- Upstream service dependencies reduced or removed where they made the project worse
- Local-first behavior wherever possible

## Provider Support

Oroboros-Anthropic Claude CLI currently supports:

- Anthropic login and API key flows
- OpenAI API keys
- OpenAI Codex login import and refresh flow
- OpenRouter API keys

Default endpoints:

- OpenAI base URL: `https://api.openai.com/v1`
- OpenAI websocket mode endpoint: `wss://api.openai.com/v1/responses`
- OpenRouter Anthropic-compatible base URL: `https://openrouter.ai/api`
- OpenRouter Responses API: `https://openrouter.ai/api/v1/responses`

## Quick Start

1. Run `claude-cli`
2. Run `/login`
3. Pick your provider and complete the flow
4. Run `/status` to confirm the active provider and auth method

The intended setup path is inside the CLI itself. Environment variables still work, but they are mostly useful for CI, headless usage, forced provider selection, or custom/proxied endpoints.

## Environment Examples

OpenAI:

```bash
CLAUDE_CLI_API_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

OpenRouter:

```bash
CLAUDE_CLI_API_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api
```

## What You Get

- Better provider freedom
- Better performance than the original Claude Code across startup, idle usage, and long sessions
- OpenAI and OpenRouter support without weird bolt-on hacks
- Less phone-home behavior
- A CLI that feels more practical, more open, and more yours

## Project Direction

The direction is straightforward:

- Keep the parts of Claude Code that were actually good
- Remove the parts that made it annoying, restrictive, or bloated
- Support multiple providers without making daily usage worse
- Keep the project useful instead of over-managed

If you liked the original idea but got tired of the lock-in, this is the fork.

## Disclaimer

Oroboros-Anthropic Claude CLI is an independent, unofficial community project and is not affiliated with, endorsed by, or sponsored by Anthropic, PBC.

`Claude`, `Claude Code`, and related names, marks, and branding are the property of Anthropic, PBC or their respective owners. They are referenced here only to describe compatibility, origin, and the purpose of this fork.

The intent here is interoperability, commentary, and fair reference, not impersonation.
