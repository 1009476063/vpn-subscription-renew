#!/bin/bash
# 本机定时刷新快猫订阅到 Gist（主永续通道，绕过 Actions IP 封锁）
# 每次刷新成功后同步向 Uptime Kuma 推送健康心跳
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/refresh.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')
PUSH_URL="http://129.146.99.81:8068/api/push/km_renew_push_129146252112_sync"

TOKEN=$(/opt/homebrew/bin/gh auth token 2>/dev/null || gh auth token 2>/dev/null)
if [ -z "$TOKEN" ]; then
  echo "$TS ERROR: no gh token" >> "$LOG"
  exit 1
fi
cd "$DIR" || exit 1
GIST_TOKEN="$TOKEN" GIST_ID="98ee639023acbec7a4b086cc87cd2de7" /usr/bin/python3 "$DIR/vpn_refresher.py" >> "$LOG" 2>&1
RC=$?
if [ $RC -ne 0 ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] First attempt failed (rc=$RC), retrying in 10s..." >> "$LOG"
  sleep 10
  GIST_TOKEN="$TOKEN" GIST_ID="98ee639023acbec7a4b086cc87cd2de7" /usr/bin/python3 "$DIR/vpn_refresher.py" >> "$LOG" 2>&1
  RC=$?
fi

if [ $RC -eq 0 ]; then
  curl -s -m 8 "${PUSH_URL}?status=up&msg=Mac_synced_OK&ping=1" >/dev/null 2>&1 || true
fi

# 日志滚动防爆盘：超过 5000 行保留最近 3000 行
if [ -f "$LOG" ] && [ $(wc -l < "$LOG") -gt 5000 ]; then
  tail -n 3000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

echo "$TS rc=$RC (vim: $(grep -c 'DONE' "$LOG" 2>/dev/null))" >> "$LOG"
