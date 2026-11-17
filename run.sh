#!/bin/zsh
# usage: ./run.sh [--dry]
cd "$(dirname "$0")" || exit 1
mkdir -p logs; exec >> logs/run.log 2>&1
echo "== $(date)"
set -a; [ -f .env ] && . ./.env; set +a
export DRY_RUN=0; [ "$1" = "--dry" ] && export DRY_RUN=1
mkdir -p data
python3 tools/healthcheck.py
[ -f .sync-graph ] && git pull --rebase --quiet 2>/dev/null
PROMPT=$(sed "s/\${DRY_RUN}/$DRY_RUN/" prompts/loop.md)
claude -p "$PROMPT" --mcp-config mcp.json \
  --permission-mode acceptEdits --max-turns 80 \
  --allowedTools "mcp__browser" "Read" "Edit(profile_cache.json)" \
    "Bash(python3 tools/*)" "Bash(date*)" "Bash(echo *)" "Bash(cat *)" \
  --disallowedTools "Bash(rm *)" "Bash(git *)" "Bash(curl *)" "Bash(wget *)" "Bash(gh *)" "Bash(sudo *)" "WebFetch" \
  || python3 tools/healthcheck.py fail claude "Claude Code run failed (login expired?). Run: claude /login, then check logs/run.log"
python3 tools/learn.py > /dev/null
python3 tools/compact.py
# Graph sync is opt-in: only if you created .sync-graph AND pointed origin at YOUR PRIVATE repo.
if [ -f .sync-graph ]; then
  git add -f data learned.json && git commit -qm "run $(date +%F-%H%M)"
  git push --quiet || python3 tools/healthcheck.py fail push "Graph push failed. Check gh auth status / repo remote."
fi
echo "== done in ${SECONDS}s"
