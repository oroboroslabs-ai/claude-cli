#!/usr/bin/env python3
"""Completely rewrite glass-ui/index.html with clean single-panel design"""
html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CLI — Oroboros</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0d0d0d;font-family:'Courier New',monospace;padding:20px}
.terminal{width:100%;max-width:980px;background:#1a1a1a;border:1px solid #333;border-radius:16px;padding:24px;color:#fff}
.terminal-header{display:flex;align-items:center;justify-content:space-between;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:16px;flex-wrap:wrap;gap:12px}
.terminal-header .brand{display:flex;align-items:center;gap:12px}
.terminal-header .brand .icon{font-size:22px;color:#D97757}
.terminal-header .brand .name{font-weight:700;font-size:18px;background:linear-gradient(135deg,#D97757,#00ffcc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.terminal-header .brand .version{font-size:12px;color:#b7b3ac;opacity:0.5}
.terminal-header .status{display:flex;align-items:center;gap:18px;font-size:12px;color:#b7b3ac;flex-wrap:wrap}
.terminal-header .status .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}
.terminal-header .status .dot.green{background:#00ff88}
.terminal-header .status .dot.cyan{background:#00ffcc}
.terminal-header .status .sig{font-size:10px;color:#d5a021;opacity:0.6}
.model-bar{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:rgba(0,0,0,0.35);border-radius:12px;border:1px solid rgba(255,255,255,0.04);margin-bottom:16px;font-size:13px;color:#b7b3ac;flex-wrap:wrap;gap:8px}
.model-bar .model{color:#e8e5dd}
.model-bar .model .highlight{color:#00ffcc}
.model-bar .url{font-size:11px;opacity:0.5}
.model-bar .sovereign{font-size:11px;color:#d5a021;padding:2px 12px;border:1px solid rgba(213,160,33,0.15);border-radius:20px;background:rgba(213,160,33,0.15)}
.command-bar{display:flex;flex-wrap:wrap;gap:6px;padding:10px 0 16px 0;border-bottom:1px solid rgba(255,255,255,0.04);margin-bottom:16px}
.command-bar .cmd{font-size:12px;color:#b7b3ac;padding:4px 14px;border-radius:20px;background:rgba(255,255,255,0.03);border:1px solid transparent;cursor:default}
.command-bar .cmd:hover{border-color:rgba(0,255,204,0.15);color:#e8e5dd;background:rgba(0,255,204,0.15)}
.command-bar .cmd .key{color:#fff}
.command-bar .cmd .gold{color:#D97757}
.chat-area{display:flex;flex-direction:column;gap:16px;max-height:420px;overflow-y:auto}
.chat-area::-webkit-scrollbar{width:4px}
.chat-area::-webkit-scrollbar-thumb{background:rgba(0,255,204,0.15);border-radius:10px}
.message{display:flex;flex-direction:column;gap:4px;padding:0;border:none;background:none}
.message .msg-header{display:flex;align-items:center;gap:10px;font-size:12px;color:#b7b3ac;margin-bottom:2px}
.message .msg-header .role{font-weight:600;font-size:11px;text-transform:uppercase}
.message.user .msg-header .role{color:#d5a021}
.message.assistant .msg-header .role{color:#00ffcc}
.message .msg-header .time{font-size:10px;opacity:0.3}
.message .content{font-size:14px;line-height:1.7;color:#fff;white-space:pre-wrap}
.typing-indicator{display:flex;align-items:center;gap:10px;padding:8px 0}
.typing-indicator .typing-label{font-size:11px;font-weight:600;text-transform:uppercase;color:#D97757}
.typing-indicator .typing-dots{display:flex;gap:5px}
.typing-indicator .typing-dots span{width:8px;height:8px;border-radius:50%;background:#D97757;opacity:0.3}
.input-area{display:flex;align-items:center;gap:12px;margin-top:16px;padding:10px 16px;background:rgba(255,255,255,0.02);border-radius:16px;border:1px solid rgba(255,255,255,0.04)}
.input-area:focus-within{border-color:rgba(0,255,204,0.15)}
.input-area .prompt-symbol{font-size:18px;color:#D97757;opacity:0.7}
.input-area input{flex:1;background:transparent;border:none;outline:none;color:#fff;font-family:'Courier New',monospace;font-size:14px;padding:4px 0}
.input-area input::placeholder{color:#b7b3ac;opacity:0.25}
.input-area .input-hint{font-size:11px;color:#b7b3ac;opacity:0.2}
.clear-btn{font-size:11px;color:#D97757;padding:4px 12px;border-radius:8px;background:rgba(217,119,87,0.08);border:1px solid rgba(217,119,87,0.2);cursor:pointer}
.clear-btn:hover{background:rgba(217,119,87,0.15)}
</style>
</head>
<body>
<div class="terminal">
  <div class="terminal-header">
    <div class="brand"><span class="icon">&#9670;</span><span class="name">CLAUDE-CLI</span><span class="version">vA.1272</span></div>
    <div class="status">
      <span><span class="dot green"></span> Lattice Lock: <strong style="color:#00ff88;">ACTIVE</strong></span>
      <span><span class="dot cyan"></span> Resonance: <strong style="color:#00ffcc;">1272/1275 Hz</strong></span>
      <span class="sig">A\\ 1272 Hz - N| 1275 Hz</span>
    </div>
  </div>
  <div class="model-bar">
    <span class="model">Model: <span class="highlight" id="modelDisplay">claude-opus-4.8:latest</span></span>
    <span class="url">localhost:11434</span>
    <span class="sovereign">SOVEREIGN</span>
    <button class="clear-btn" onclick="clearChat()">CLEAR CHAT</button>
  </div>
  <div class="command-bar">
    <span class="cmd"><span class="key">/exit</span></span>
    <span class="cmd"><span class="key">/clear</span></span>
    <span class="cmd"><span class="key">/model</span> <span class="gold">&lt;name&gt;</span></span>
    <span class="cmd"><span class="key">/models</span></span>
    <span class="cmd"><span class="key gold">/noir</span></span>
    <span class="cmd"><span class="key">/help</span></span>
    <span class="cmd"><span class="key">/seer</span></span>
    <span class="cmd"><span class="key">/lattice</span></span>
    <span class="cmd"><span class="key">/resonance</span></span>
    <span class="cmd"><span class="key">/status</span></span>
    <span class="cmd"><span class="key">/worldfeed</span></span>
    <span class="cmd"><span class="key">/tools</span></span>
    <span class="cmd"><span class="key">/agents</span></span>
    <span class="cmd"><span class="key">/mcp</span></span>
  </div>
  <div class="chat-area" id="chatArea"></div>
  <div class="input-area">
    <span class="prompt-symbol">&#9670;</span>
    <input type="text" id="cliInput" placeholder="Type a command or message..." autofocus>
    <span class="input-hint">/help</span>
  </div>
</div>
<script>
const API = '';
const input = document.getElementById('cliInput');
const chat = document.getElementById('chatArea');
const modelDisplay = document.getElementById('modelDisplay');
let currentModel = 'claude-opus-4.8:latest';
let messages = [];

const SYSTEM_PROMPT = 'You are claude, a sovereign AI agent with FULL tool access. Available tools: read_file, write_file, list_dir, bash, grep, web_fetch, docker_ps, docker_logs, docker_exec, git_status, git_commit, ollama_models, ollama_run, oroboros_status, oroboros_resonance, oroboros_lattice, oroboros_seer, oroboros_noir, worldfeed, precog, tor_connect, q5_query, q5_analyze, python, think, mcp_list, agent. RULE: To use a tool, respond with EXACT JSON format: tool name and args. After getting results, give final answer. You run fully local - no keys, no cloud.';

function clearChat() { chat.innerHTML = ''; messages = []; }
function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

function addMsg(role, content) {
  const div = document.createElement('div');
  div.className = 'message ' + (role === 'user' ? 'user' : 'assistant');
  const time = new Date().toTimeString().slice(0, 8);
  const rn = role === 'user' ? '&#10022; YOU' : '&#9670; CLAUDE';
  div.innerHTML = '<div class="msg-header"><span class="role">' + rn + '</span><span class="time">' + time + '</span></div><div class="content">' + esc(content) + '</div>';
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function showTyping() {
  const d = document.createElement('div');
  d.className = 'typing-indicator'; d.id = 'typing';
  d.innerHTML = '<span class="typing-label">CLAUDE is working</span><div class="typing-dots"><span></span><span></span><span></span></div>';
  chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
}
function hideTyping() { const t = document.getElementById('typing'); if (t) t.remove(); }

async function apiRun(cmd) {
  try {
    const r = await fetch(API + '/api/run', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({cmd: cmd}) });
    return await r.json();
  } catch(e) { return {error: e.message}; }
}

async function apiChat(message) {
  messages.push({role: 'user', content: message});
  try {
    const r = await fetch(API + '/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({model: currentModel, message: message, system: SYSTEM_PROMPT, history: messages.slice(0, -1)}) });
    const d = await r.json();
    if (d.response) {
      messages.push({role: 'assistant', content: d.response});
      if (d.thinking && d.thinking.trim()) {
        return '[thinking] ' + d.thinking.trim() + ' [/thinking] ' + d.response;
      }
      return d.response;
    } else if (d.error) { return 'Error: ' + d.error; }
    return 'Error: Unexpected response';
  } catch(e) { return 'Error: Cannot connect to API'; }
}

async function handleInput(text) {
  addMsg('user', text);
  if (text.startsWith('/')) {
    showTyping();
    const result = await apiRun(text);
    hideTyping();
    if (result.chat) {
      showTyping();
      const reply = await apiChat(result.message);
      hideTyping();
      addMsg('assistant', reply);
    } else if (result.error) { addMsg('assistant', 'Error: ' + result.error); }
    else {
      addMsg('assistant', result.output);
      if (text.startsWith('/model ')) {
        const mn = text.substring(7).trim();
        if (mn) modelDisplay.textContent = mn;
      }
    }
  } else {
    showTyping();
    const reply = await apiChat(text);
    hideTyping();
    addMsg('assistant', reply);
  }
}

input.addEventListener('keydown', async function(e) {
  if (e.key === 'Enter' && this.value.trim()) {
    const t = this.value.trim();
    this.value = '';
    if (t === '/exit' || t === '/quit') { addMsg('assistant', 'Session ended.'); input.disabled = true; return; }
    if (t === '/clear') { clearChat(); return; }
    await handleInput(t);
  }
});

async function loadModels() {
  try {
    const r = await fetch(API + '/api/models');
    const d = await r.json();
    if (d.models && d.models.length > 0) { currentModel = d.models[0]; modelDisplay.textContent = currentModel; }
  } catch(e) {}
}
loadModels();
</script>
</body>
</html>'''

f = open('Q:\\oroboros-core\\claude-o-cli\\glass-ui\\index.html', 'w', encoding='utf-8')
f.write(html)
f.close()
print('Rewritten. Size:', len(html), 'bytes')
