#!/bin/sh
# 快猫订阅自动刷新到 Gist（Linux 服务器独立运行脚本）
# 内置 Anti-Ban Jitter 随机时间扰动机制，避免固定秒级请求被上游识别
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/refresh.log"
TS=$(date "+%Y-%m-%d %H:%M:%S")

# 随机扰动 5~45 秒（外部手动执行时可通过传入 nojitter 跳过）
if [ "$1" != "nojitter" ]; then
    JITTER=$(( (RANDOM % 41) + 5 ))
    sleep "$JITTER"
fi

if [ -f "$DIR/.env" ]; then
    . "$DIR/.env"
fi

if [ -z "$GIST_TOKEN" ] || [ -z "$GIST_ID" ]; then
    echo "$TS [ERROR] GIST_TOKEN or GIST_ID not configured" >> "$LOG"
    exit 1
fi

cd "$DIR" || exit 1
export GIST_TOKEN GIST_ID
python3 "$DIR/vpn_refresher.py" >> "$LOG" 2>&1
RC=$?

# 日志滚动防爆盘：超过 5000 行保留最近 3000 行
if [ -f "$LOG" ] && [ $(wc -l < "$LOG") -gt 5000 ]; then
    tail -n 3000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

echo "$TS [RUN] rc=$RC (done_count: $(grep -c 'DONE' "$LOG" 2>/dev/null))" >> "$LOG"
exit $RC
