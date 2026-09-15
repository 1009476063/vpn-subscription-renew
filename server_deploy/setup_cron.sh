#!/bin/sh
# 一键安装 Crontab 定时任务（每 13 分钟执行一次，结合脚本内随机 5~45s Jitter）
DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_CMD="*/13 * * * * $DIR/refresh.sh >/dev/null 2>&1"

crontab -l 2>/dev/null > /tmp/current_cron || true
if grep -Fq "$DIR/refresh.sh" /tmp/current_cron 2>/dev/null; then
    echo "[INFO] Crontab job already exists."
else
    echo "$CRON_CMD" >> /tmp/current_cron
    crontab /tmp/current_cron
    echo "[SUCCESS] Crontab job installed successfully:"
    crontab -l | grep "$DIR/refresh.sh"
fi
rm -f /tmp/current_cron
