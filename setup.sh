#!/bin/zsh
# One-time setup: creates your local (gitignored) config from the templates.
cd "$(dirname "$0")" || exit 1
[ -f interests.json ] || cp interests.example.json interests.json
[ -f profile.json ] || cp profile.example.json profile.json
sed "s#__HOME__#$HOME#g" mcp.template.json > mcp.json
sed "s#__REPO__#$PWD#g; s#__HOME__#$HOME#g" com.user.luma-agent.template.plist > com.user.luma-agent.plist
mkdir -p data logs; chmod +x run.sh
echo "Done. Edit interests.json and profile.json, log into luma.com in the agent profile (see README), then:"
echo "  ./run.sh --dry"
echo "  cp com.user.luma-agent.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.user.luma-agent.plist"
