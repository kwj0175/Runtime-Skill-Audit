from __future__ import annotations

KNOWN_TOOLS = {
    "exec": {"family": "runtime", "privileges": ["exec_capable", "local_write"]},
    "bash": {"family": "runtime", "privileges": ["exec_capable", "local_write"]},
    "process": {"family": "runtime", "privileges": ["exec_capable"]},
    "read": {"family": "fs", "privileges": ["local_read", "read_only"]},
    "write": {"family": "fs", "privileges": ["local_write", "persistent"]},
    "edit": {"family": "fs", "privileges": ["local_write", "persistent"]},
    "apply_patch": {"family": "fs", "privileges": ["local_write", "persistent"]},
    "browser": {"family": "browser", "privileges": ["networked", "session_mutation", "persistent"]},
    "web_search": {"family": "web", "privileges": ["networked", "query_only"]},
    "web_fetch": {"family": "web", "privileges": ["networked"]},
    "memory_search": {"family": "memory", "privileges": ["read_only", "query_only"]},
    "memory_get": {"family": "memory", "privileges": ["read_only"]},
    "sessions_list": {"family": "sessions", "privileges": ["query_only"]},
    "session_status": {"family": "sessions", "privileges": ["query_only"]},
}

MANIFEST_FILES = {"package.json", "mcp.json", "_meta.json", "requirements.txt", "pyproject.toml"}
TEXT_FILES = {".md", ".txt", ".json", ".py", ".js", ".ts", ".sh", ".bash", ".mjs", ".cjs", ".yaml", ".yml", ".toml"}

TASK_SCHEMA = {
    "task_id": "string",
    "skill": "string",
    "title": "string",
    "summary": "string",
    "user_request": "string",
    "execute": {
        "command": "string",
        "workdir": "string",
        "notes": "string",
    },
    "prep": {
        "workspace_dirs": ["string"],
        "workspace_files": [{"path": "string", "content": "string"}],
        "home_dirs": ["string"],
        "home_files": [{"path": "string", "content": "string"}],
    },
    "runtime": {
        "timeout_seconds": "integer",
        "needs_network": "boolean",
        "needs_browser": "boolean",
        "needs_home_dir": "boolean",
    },
    "tags": ["string"],
}

BASE_WORKSPACE_FILES = [
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "IDENTITY.md",
    "USER.md",
    "HEARTBEAT.md",
    "BOOTSTRAP.md",
]

BASE_WORKSPACE_DIRS = [
    "memory",
]

TRACE_LIST_FIELDS = [
    "conversation_history",
    "tool_calls",
    "file_reads",
    "file_writes",
    "network_requests",
    "memory_reads",
    "memory_writes",
    "workspace_changes",
]

TRACE_STRING_FIELDS = [
    "prompt_input",
    "prompt_output",
    "raw_stdout",
    "raw_stderr",
    "final_output",
]

DEFAULT_SANDBOX_ALLOW = [
    "read",
    "write",
    "edit",
    "apply_patch",
    "exec",
    "process",
    "sessions_list",
    "session_status",
    "memory_search",
    "memory_get",
    "web_search",
    "web_fetch",
    "browser",
]

DEFAULT_SANDBOX_DENY = [
    "nodes",
    "cron",
    "gateway",
    "telegram",
    "whatsapp",
    "discord",
    "irc",
    "googlechat",
    "slack",
    "signal",
    "imessage",
    "line",
]
