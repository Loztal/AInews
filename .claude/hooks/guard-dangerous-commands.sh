#!/bin/bash
# PreToolUse hook: Block destructive shell commands.

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Block force push
if echo "$command" | grep -qE 'git\s+push\s+.*--force'; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Force push is blocked. Use regular push or ask the user first."}}
EOF
  exit 0
fi

# Block rm -rf on project directories
if echo "$command" | grep -qE 'rm\s+-rf\s+(/home/user/AInews/?|\./?|scraper/?|docs/?|tests/?)'; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Recursive deletion of project directories is blocked."}}
EOF
  exit 0
fi

echo '{}'
exit 0
