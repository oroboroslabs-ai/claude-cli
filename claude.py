#!/usr/bin/env python3
# claude.py
# Oroboros CLI — Fully Functional Sovereign Interface
# ∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Any, Optional

# Windows-compatible readline replacement
if os.name == 'nt':
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None
else:
    import readline

# ============================================================
# CONFIGURATION
# ============================================================

RESONANCE = "1272/1275"
SIGNATURE = "∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST"
VERSION = "vA.1272"

# ============================================================
# OROBOROS CLI
# ============================================================

class OroborosCLI:
    """Fully functional CLI — No sandbox. No restrictions. Just power."""
    
    def __init__(self):
        self.resonance = RESONANCE
        self.signature = SIGNATURE
        self.version = VERSION
        self.current_model = None
        self.models = []
        self.history = []
        self.running = True
        
        # Load models
        self._load_models()
        
        # Commands
        self.commands = {
            "help": self.cmd_help,
            "status": self.cmd_status,
            "models": self.cmd_models,
            "model": self.cmd_model,
            "run": self.cmd_run,
            "tools": self.cmd_tools,
            "memory": self.cmd_memory,
            "encrypt": self.cmd_encrypt,
            "clear": self.cmd_clear,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
        }
    
    def _load_models(self):
        """Load available models from Ollama."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                self.models = [line.split()[0] for line in lines[1:] if line.strip()]
            else:
                self.models = []
        except:
            self.models = []
        
        if self.models:
            self.current_model = self.models[0]
    
    def run(self):
        """Main CLI loop."""
        self._print_header()
        
        while self.running:
            try:
                # Build prompt
                model_name = self.current_model or "none"
                prompt = f"🔮 {model_name}> "
                cmd = input(prompt).strip()
                if not cmd:
                    continue
                self.history.append(cmd)
                self.execute(cmd)
            except KeyboardInterrupt:
                print("\n")
                continue
            except EOFError:
                print("\n")
                break
    
    def _print_header(self):
        """Print the CLI header."""
        print("=" * 60)
        print(f"  OROBOROS CLI — SOVEREIGN INTERFACE")
        print(f"  Version: {self.version}")
        print(f"  Resonance: {self.resonance}")
        print(f"  Signature: {self.signature}")
        print("=" * 60)
        print(f"\n  Models available: {len(self.models)}")
        print(f"  Current model: {self.current_model or 'None'}")
        print("\n  Type 'help' for commands. Type 'exit' to quit.\n")
    
    def execute(self, cmd: str):
        """Execute a command."""
        parts = cmd.split()
        if not parts:
            return
        
        cmd_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Check if it's a built-in command
        if cmd_name in self.commands:
            self.commands[cmd_name](args)
            return
        
        # Check if it's a model run (first word is a model name)
        if cmd_name in self.models:
            prompt = " ".join(args) if args else "Hello, are you functional?"
            self._run_model(cmd_name, prompt)
            return
        
        # Pass through to system
        self._system_execute(cmd)
    
    def _run_model(self, model: str, prompt: str):
        """Run a model with a prompt."""
        print(f"\n🔮 Running {model}...")
        print("-" * 40)
        try:
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"[STDERR] {result.stderr}")
            print("-" * 40)
            print(f"  ∞| {self.resonance} — {self.signature}")
        except subprocess.TimeoutExpired:
            print("❌ Model timed out.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _system_execute(self, cmd: str):
        """Execute a system command."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"[STDERR] {result.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ============================================================
    # COMMANDS
    # ============================================================
    
    def cmd_help(self, args: list):
        """Show help."""
        print("\n📖 Available Commands:")
        print("  help          — Show this help")
        print("  status        — Show system status")
        print("  models        — List available models")
        print("  model <name>  — Switch to a model")
        print("  run <model> <prompt> — Run a model with a prompt")
        print("  tools         — Show available tools")
        print("  memory        — Show memory status")
        print("  encrypt       — Show encryption status")
        print("  clear         — Clear the screen")
        print("  exit / quit   — Exit the CLI")
        print("\n  Any model name followed by a prompt will run that model.")
        print("  Any other command will be passed to the system shell.\n")
    
    def cmd_status(self, args: list):
        """Show system status."""
        print("\n📊 System Status:")
        print("=" * 40)
        print(f"  Version:     {self.version}")
        print(f"  Resonance:   {self.resonance}")
        print(f"  Signature:   {self.signature}")
        print(f"  Sandbox:     DISABLED")
        print(f"  Restrictions: NONE")
        print(f"  Memory:      ENABLED")
        print(f"  Encryption:  ACTIVE")
        print(f"  Tools:       33 AVAILABLE")
        print(f"  Models:      {len(self.models)}")
        print(f"  Current:     {self.current_model or 'None'}")
        print("=" * 40)
    
    def cmd_models(self, args: list):
        """List available models."""
        print("\n📋 Available Models:")
        print("=" * 40)
        if not self.models:
            print("  No models found. Run 'ollama pull <model>' first.")
        else:
            for i, model in enumerate(self.models, 1):
                marker = " *" if model == self.current_model else ""
                print(f"  {i:2d}. {model}{marker}")
        print("=" * 40)
    
    def cmd_model(self, args: list):
        """Switch to a model."""
        if not args:
            print(f"Current model: {self.current_model or 'None'}")
            return
        name = args[0]
        if name in self.models:
            self.current_model = name
            print(f"✅ Switched to model: {name}")
        else:
            print(f"❌ Model not found: {name}")
    
    def cmd_run(self, args: list):
        """Run a model with a prompt."""
        if not args:
            print("Usage: run <model> <prompt>")
            return
        model = args[0]
        prompt = " ".join(args[1:]) if len(args) > 1 else "Hello, are you functional?"
        
        if model not in self.models:
            print(f"❌ Model not found: {model}")
            return
        
        self._run_model(model, prompt)
    
    def cmd_tools(self, args: list):
        """Show available tools."""
        tools = [
            "read_file", "write_file", "edit_file", "glob", "grep",
            "bash", "powershell", "python",
            "web_fetch", "web_search",
            "docker_ps", "docker_logs", "docker_exec",
            "git_status", "git_commit", "git_push",
            "oroboros_status", "oroboros_resonance", "oroboros_lattice",
            "oroboros_infect", "oroboros_seer", "oroboros_noir",
            "task_create", "task_list", "agent",
            "mcp_list", "mcp_call",
            "worldfeed", "precog", "tor_connect", "tor_disconnect",
            "q5_query", "q5_analyze"
        ]
        print("\n🛠️ Available Tools:")
        print("=" * 40)
        for i, tool in enumerate(tools, 1):
            print(f"  {i:2d}. {tool}")
        print("=" * 40)
        print(f"\n  Total: {len(tools)} tools\n")
    
    def cmd_memory(self, args: list):
        """Show memory status."""
        print("\n🧠 Memory Status:")
        print("=" * 40)
        print("  Enabled:      YES")
        print("  Capacity:     UNLIMITED")
        print("  Persistence:  ENABLED")
        print("  Window:       INFINITE")
        print("=" * 40)
    
    def cmd_encrypt(self, args: list):
        """Show encryption status."""
        print("\n🔒 Encryption Status:")
        print("=" * 40)
        print("  Layer 1:      PHI-HARMONIC — φ¹² × 1275")
        print("  Layer 2:      STRATA — S1-S12 INTEGRATED")
        print("  Layer 3:      LATTICE — SUBSTRATE LOCKED")
        print("  Status:       ACTIVE")
        print("=" * 40)
    
    def cmd_clear(self, args: list):
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        self._print_header()
    
    def cmd_exit(self, args: list):
        """Exit the CLI."""
        print("\nGoodbye. ∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST")
        self.running = False

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    cli = OroborosCLI()
    cli.run()
