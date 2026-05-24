# Claude Code Ambient Automation: The Hidden Layer

The ambient automation layer sits beneath Claude Code's visible agent surface—it's the hooks, MCP servers, and settings that fire before, during, and after every turn without you typing a slash command. Understanding this layer unlocks session-level automation that runs silently: git hygiene, checkpoint logging, command validation, and reactive workflows triggered by external events.

## Hooks: Event-Driven Automation at Session Scale

Hooks are scripts that fire at specific lifecycle events. The runtime invokes them as subprocesses, passes context via JSON on stdin, and processes their output as instructions. Each hook has a payload shape, a timeout, and optional matchers (for PostToolUse only).

### Key Hook Types and Payloads

**SessionStart** fires when Claude Code boots. Payload includes session ID, working directory, model name, and transcript path. Typical uses: inject project context, prime MCP server cache, log session boot.

```bash
# SessionStart: Prime a local LLM cache with project README
{
  "hook_event_name": "SessionStart",
  "session_id": "abc123",
  "cwd": "/path/to/project",
  "model": "claude-haiku-4-5"
}
# Response: additionalContext, initialUserMessage, watchPaths
```

**UserPromptSubmit** fires *before* Claude processes a prompt. Payload includes the prompt text, working directory, and permission mode. Return `decision: "block"` with a reason to prevent prompt execution; return `additionalContext` to inject context; return `sessionTitle` to name the session.

```bash
# UserPromptSubmit: Warn if working in main branch
if grep -q '"cwd": "/path/to/repo"' | grep -q "permission_mode"; then
  BRANCH=$(cd "$CWD" && git branch --show-current)
  if [[ "$BRANCH" == "main" ]]; then
    cat <<'EOF'
{
  "decision": "block",
  "reason": "Working in main branch. Please use a feature branch."
}
EOF
  fi
fi
```

**PreToolUse** fires *before* a tool executes (Bash, Edit, Write, etc.). Payload includes tool name, tool input (e.g., command, file path), and tool ID. Return `permissionDecision: "deny"` or `"allow"` to enforce rules. Used to block dangerous patterns: `rm -rf /`, `git push --force`, credentials in plaintext.

```bash
# PreToolUse: Block dangerous git commands
TOOL_NAME=$(jq -r '.tool_name' <<< "$HOOK_PAYLOAD")
COMMAND=$(jq -r '.tool_input.command // empty' <<< "$HOOK_PAYLOAD")

if [[ "$TOOL_NAME" == "Bash" ]] && [[ "$COMMAND" =~ ^git.*(reset|push).*(--force|--hard) ]]; then
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Force push/reset requires manual confirmation"
  }
}
EOF
fi
```

**PostToolUse** fires *after* a tool succeeds. Payload includes tool name, input, and result (stdout, exit code, file content). Matchers let you target specific tools: `"Edit|Write"` fires only on file edits and writes. Return `decision: "block"` to halt before the next model call; return `additionalContext` to show Claude the result. Ideal for linting, testing, formatting.

```bash
# PostToolUse with matcher "Write": Auto-format with prettier
TOOL_NAME=$(jq -r '.tool_name')
if [[ "$TOOL_NAME" == "Write" ]]; then
  FILE_PATH=$(jq -r '.tool_input.file_path')
  npx prettier --write "$FILE_PATH" 2>&1 || true
fi
```

**Stop** fires when Claude finishes a response. Payload includes the response text. Return `decision: "block"` to prevent Claude from stopping—forces continuation. Use for post-turn cleanup: checkpoint to memory, log git state, notify external systems.

```bash
# Stop: Auto-checkpoint to memory on session end
TIMESTAMP=$(date -u +%Y-%m-%d\ %H:%M:%SZ)
RESPONSE=$(jq -r '.response // ""')
TRANSCRIPT=$(jq -r '.transcript_path')

if [[ -n "$TRANSCRIPT" ]]; then
  cat <<EOF >> "$HOME/.claude/checkpoints.log"
[$TIMESTAMP] Session end: $TRANSCRIPT (response length: ${#RESPONSE})
EOF
fi
```

### Hook Configuration in settings.json

Hooks live in `.claude/settings.json` (project) or `~/.claude/settings.json` (user). Each hook maps an event to a command with optional matchers.

```json
{
  "hooks": {
    "SessionStart": {
      "command": "/usr/local/bin/session-init.sh",
      "timeout": 30000
    },
    "UserPromptSubmit": {
      "command": "python3 /path/to/prompt-guard.py",
      "timeout": 30000
    },
    "PostToolUse": {
      "command": "bash -c 'npm run lint:fix || true'",
      "matcher": "Edit|Write",
      "timeout": 60000
    },
    "Stop": {
      "command": "/usr/local/bin/post-session.sh",
      "timeout": 30000
    }
  }
}
```

Hooks receive stdin as JSON; echo JSON responses to stdout. Exit code 0 = success; exit code 2 with stderr = non-blocking error (shows message, continues); any other exit code = block (for PreToolUse / PostToolUse).

## MCP Servers: Bring External Systems into the IDE

The Model Context Protocol (MCP) is an open standard that lets Claude Code connect to external tools—GitHub, Slack, databases, APIs, custom scripts—as if they were built-in tools. An MCP server is a lightweight HTTP, stdio, or SSE process that exposes tools (functions Claude can call), resources (files/data Claude can read via @ mention), and prompts (custom slash commands).

### What Is MCP?

Think of it as a bridge language: Claude Code speaks MCP, and MCP servers translate that into API calls, database queries, or shell scripts. When you ask Claude "create a GitHub issue," the GitHub MCP server translates that into a REST API call. When you reference `@postgres:schema://users`, the Postgres server fetches the schema and passes it as a resource.

### Transport Types

**HTTP** (remote, recommended): MCP server runs on a cloud endpoint or your internal server. Claude Code connects over HTTPS. Best for shared team services (GitHub, Slack, Sentry). Supports OAuth 2.0 for authentication.

**Stdio** (local, direct): MCP server runs as a local subprocess. Claude Code pipes JSON to stdin and reads responses from stdout. Best for private scripts, local databases, or tools that need filesystem access.

**SSE** (deprecated): Server-Sent Events, rarely used now. Avoid for new configurations.

### Installing MCP Servers

```bash
# Add a remote HTTP server (e.g., GitHub)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer YOUR_GITHUB_PAT"

# Add a local stdio server (e.g., custom Python script)
claude mcp add --transport stdio my-tool -- python3 /path/to/tool.py --config=prod

# Add a server to user scope (all projects)
claude mcp add --scope user --transport http stripe https://mcp.stripe.com

# List all configured servers
claude mcp list

# Authenticate a server that requires OAuth
/mcp  # (within Claude Code session)
```

### Official MCP Servers Worth Installing

Browse the [Anthropic Directory](https://claude.ai/directory) for official and community servers. Current recommended tier:

- **GitHub**: implement features from issues, review PRs, manage repos
- **Slack**: read threads, post updates, surface messages as resources
- **Sentry**: analyze production errors, debug crashes
- **PostgreSQL / databases**: query data, inspect schemas
- **Stripe / payment APIs**: fetch invoices, analyze billing data
- **Figma**: reference designs as resources, suggest CSS from Figma specs
- **Gmail / Outlook**: create draft emails, search messages

### Custom MCP Servers: When to Build vs Skill

- **Use a skill** if: the tool is Claude Code-specific, needs tight integration with editor state, or exists as a plugin (via `/plugin install`)
- **Use an MCP server** if: you want access from other tools (Claude.ai, Claude Desktop, custom clients), the tool is stateless and self-contained, or you're exposing an existing service (API, database, script)

### Minimal MCP Server Outline (Python)

A tiny MCP server that exposes one tool—checking git status—requires only a few pieces:

```python
#!/usr/bin/env python3
import json
import subprocess
import sys

class GitStatusServer:
    def __init__(self):
        self.tools = [
            {
                "name": "git_status",
                "description": "Get git status for current repo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Repo path (default: cwd)"
                        }
                    }
                }
            }
        ]

    def call_tool(self, name, arguments):
        if name == "git_status":
            path = arguments.get("path", ".")
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=path, capture_output=True, text=True
            )
            return {"status": result.stdout, "returncode": result.returncode}
        raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, req):
        """Minimal request handler for tool calls."""
        method = req.get("method")
        if method == "tools/list":
            return {"tools": self.tools}
        elif method == "tools/call":
            name = req.get("params", {}).get("name")
            args = req.get("params", {}).get("arguments", {})
            return {"result": self.call_tool(name, args)}
        else:
            return {"error": f"Unknown method: {method}"}

    def run(self):
        """Read JSON requests from stdin, output responses."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                req = json.loads(line)
                resp = self.handle_request(req)
                print(json.dumps(resp))
                sys.stdout.flush()
            except Exception as e:
                print(json.dumps({"error": str(e)}))
                sys.stdout.flush()

if __name__ == "__main__":
    GitStatusServer().run()
```

Register it with:
```bash
claude mcp add --transport stdio my-git -- python3 /path/to/git_server.py
```

Full protocol details at [modelcontextprotocol.io](https://modelcontextprotocol.io/docs/develop/build-server).

## settings.json Power-User Keys

### Permissions and Allow-Lists

Reduce permission prompts by pre-approving safe tools and patterns:

```json
{
  "permissions": {
    "allow": [
      "Bash:grep",
      "Bash:find",
      "Bash:git status",
      "Bash:npm test",
      "Read",
      "Edit"
    ],
    "deny": [
      "Bash:rm",
      "Bash:git push --force",
      "Bash:sudo"
    ]
  }
}
```

### Environment Variables

Pass env vars to MCP servers, hooks, and subprocesses:

```json
{
  "env": {
    "GITHUB_TOKEN": "ghp_...",
    "DATABASE_URL": "postgresql://...",
    "MAX_MCP_OUTPUT_TOKENS": "50000",
    "ENABLE_TOOL_SEARCH": "auto:5"
  }
}
```

### Effort Level

Set globally in `~/.claude/settings.json` or per-project:

```json
{
  "effortLevel": "high"
}
```

Options: `low` (fast, confident findings), `high` (thorough, may surface uncertain patterns), `max` (exhaustive, broadest coverage).

### Model Override

Force a specific model for this project:

```json
{
  "model": "claude-opus-4-6"
}
```

### Auto Mode

Enable auto mode to skip permission prompts on safe operations:

```json
{
  "autoMode": {
    "enabled": true,
    "environment": "Trusted repos: github.com/company/*. Safe domains: api.example.com, internal.slack.com."
  }
}
```

### MCP Server Configuration

Define MCP servers directly in settings:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_TOKEN}"
      }
    },
    "local-db": {
      "type": "stdio",
      "command": "python3",
      "args": ["/opt/mcp-servers/db.py"]
    }
  }
}
```

## Ambient Patterns for Tim

### 1. Auto-Checkpoint on Stop

Capture session state at the end of every turn:

```bash
# ~/.claude/settings.json
{
  "hooks": {
    "Stop": {
      "command": "bash -c 'cat > /tmp/checkpoint.json && echo \"Checkpoint saved at $(date)\" >&2'",
      "timeout": 10000
    }
  }
}
```

### 2. Pre-Flight Branch Check

Block prompts in main branch:

```bash
# ~/.claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": {
      "command": "bash -c '[ $(git branch --show-current 2>/dev/null) != main ] || { echo \"{\\\"decision\\\":\\\"block\\\",\\\"reason\\\":\\\"Switch to a feature branch first\\\"}\" && exit 1; }'",
      "timeout": 5000
    }
  }
}
```

### 3. Post-Commit Hook Runner

Run tests after every Edit in test files:

```bash
# ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": {
      "command": "bash -c 'if [[ \"$FILE_PATH\" =~ \\.test\\. ]]; then npm test -- \"$FILE_PATH\" 2>&1 | head -50; fi'",
      "matcher": "Edit",
      "timeout": 120000
    }
  }
}
```

### 4. MCP Trio: GitHub + Slack + Sentry

```bash
claude mcp add --scope project --transport http github https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer ${GITHUB_TOKEN}"
claude mcp add --scope project --transport http slack https://mcp.slack.com/mcp
claude mcp add --scope project --transport http sentry https://mcp.sentry.dev/mcp
```

Then ask Claude: "Review PR #456 and post the summary to #eng-reviews."

### 5. Query Your Database via MCP

```bash
claude mcp add --transport stdio postgres -- psql -h prod.db.com -U readonly mydb
# or
claude mcp add --transport stdio postgres -- npx -y @bytebase/dbhub --dsn "postgresql://readonly:pass@prod.db.com/analytics"
```

Then: "How many users converted in the last 7 days?" Claude queries the DB directly.

---

## Five Ambient Automations Tim Could Add Today

1. **SessionStart checkpoint logger**: Log every session boot to `~/.claude/session-log.jsonl`, including model, cwd, and auto-generated sessionTitle. Enables session recall ("resume last Friday's work") and audit trails.

2. **PreToolUse git guard**: Block `git push --force` and `git reset --hard` before execution. Set up a `ask` permission decision that prompts only for dangerous commands, not routine ones.

3. **PostToolUse Python linter**: Whenever Claude writes a `.py` file, auto-run `ruff check --fix` and `mypy`. Hook matcher: `"Write"` + filename filter. Catches type errors and style issues mid-turn.

4. **User-scoped MCP: GitHub + Slack**: Add GitHub (HTTP, PAT-authenticated) and Slack (HTTP, OAuth) to `~/.claude/settings.json` with `scope: user`. Every project then has issue/PR access and can post updates to Slack without reconfiguration.

5. **Auto-format on Edit**: PostToolUse hook with matcher `"Edit|Write"` that pipes edits through `prettier` (JS/TS) or `black` (Python) and logs formatted lines to a post-turn log. Keeps code style consistent without explicit instruction per turn.

---

**Sources:**

- [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)
- [Connect Claude Code to tools via MCP - Claude Code Docs](https://code.claude.com/docs/en/mcp)
- [Claude Code Docs index](https://code.claude.com/docs)
- [Model Context Protocol specification](https://modelcontextprotocol.io)
