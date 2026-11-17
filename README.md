# Luma Event Agent

A lightweight agent that finds events on [Luma](https://luma.com) in your city, scores them against your interests, registers for the ones that qualify, asks you for quick feedback afterwards, and stores everything as a small knowledge graph.

It runs on your own Mac: a daily `launchd` job calls `claude -p` (Claude Code, headless) which drives a browser via the Playwright MCP. No server, no database, no extra API key.

## How it works
`run.sh` runs once a day:
1. **Health check:** warns (macOS notification) if GitHub, Luma or Claude logins need renewing.
2. **Discover** events on your city page, **filter** by language, **score** by your interests plus learned boosts.
3. **Book** free events with a score above the threshold (optionally submit approval requests). Answers to form questions follow [prompts/answers.md](prompts/answers.md).
4. **Feedback:** after an event, a popup asks for a 1-5 rating and one line.
5. **Learn + compact:** ratings adjust topic/host boosts (`tools/learn.py`); old noise is pruned and old history is summarised (`tools/compact.py`).

The graph is two JSONL files (`data/nodes.jsonl`, `data/edges.jsonl`). `python3 tools/viz.py` renders it as an interactive page.

## Setup
Requirements: macOS, [Claude Code](https://claude.com/claude-code) logged in, Node (for `npx`), Python 3, Brave.
```
./setup.sh                 # creates your local config from the templates
$EDITOR interests.json     # city, keywords, limits
$EDITOR profile.json       # your public LinkedIn URL
```
Log into luma.com once in the agent's own browser profile (quit with Cmd+Q afterwards so the login is saved):
```
open -na "Brave Browser" --args --user-data-dir="$HOME/.luma-agent/brave-profile" https://luma.com/signin
```
Test, then schedule:
```
./run.sh --dry
cp com.user.luma-agent.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.user.luma-agent.plist
```

## Privacy
Your profile, interests, graph and logs are gitignored, so they stay on your machine. To back the graph up to GitHub, point `origin` at **your own private** repository and run `touch .sync-graph`. Never enable that on a public remote: the graph records which events you attended and what you thought of them.

## Safety model
The agent only books free events, never answers sensitive fields (phone, ID, payment, etc.), treats web page text as data rather than instructions, and runs with an explicit tool allowlist (see `run.sh`) instead of skipping permissions.

## License
MIT
