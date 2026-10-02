#!/bin/bash
#  快猫订阅本机自动刷新 —— 一键关闭
set -u
PLIST="$HOME/Library/LaunchAgents/com.tx.sync-kuaimao.plist"
DIR="$HOME/sync-kuaimao"
echo "== 1) 卸载定时任务"
launchctl unload "$PLIST" 2>/dev/null && echo "  已卸载 com.tx.sync-kuaimao" || echo "  任务未在运行"
echo "== 2) 终止残留刷新进程（如有）"
pkill -f 'sync-kuaimao/refresh.sh' 2>/dev/null && echo "  已终止运行中的刷新" || echo "  无运行中的刷新"
echo "== 3) 完成，本机已停止自动刷新。"
echo "  如需彻底删除日志，可手动清理: $DIR/refresh.log"
