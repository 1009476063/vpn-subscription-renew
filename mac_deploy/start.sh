#!/bin/bash
# ============================================================
#  快猫订阅本机自动刷新 —— 一键开启
#  每 10 分钟调上游 API 取新订阅，更新到固定 Gist 地址，
#  同时向 Uptime Kuma 推送成功心跳，实现双保险永续。
# ============================================================
set -u
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$HOME/sync-kuaimao"
PLIST="$HOME/Library/LaunchAgents/com.tx.sync-kuaimao.plist"
GIST_ID="${GIST_ID:-98ee639023acbec7a4b086cc87cd2de7}"
PY=/usr/bin/python3

echo "== 1) 检查依赖"
command -v gh >/dev/null 2>&1 && echo "  gh:     $(command -v gh)" || { echo "  [错] 未安装 gh"; exit 1; }
TOKEN=$(gh auth token 2>/dev/null) && echo "  gh 已登录 (token 可用)" || { echo "  [错] 请先运行 gh auth login"; exit 1; }
"$PY" -c "import requests, yaml" 2>/dev/null && echo "  python3 模块: 可用" || { echo "  [错] 缺少 requests 或 pyyaml，请运行 pip3 install requests pyyaml"; exit 1; }

echo "== 2) 准备脚本目录 ($DIR)"
mkdir -p "$DIR"
cp "$REPO_DIR/mac_deploy/refresh.sh" "$DIR/refresh.sh"
cp "$REPO_DIR/vpn_refresher.py" "$DIR/vpn_refresher.py"
chmod +x "$DIR/refresh.sh" "$DIR/vpn_refresher.py"

echo "== 3) 立即手动刷新一次（验证通道可用）"
GIST_TOKEN="$TOKEN" GIST_ID="$GIST_ID" "$PY" "$DIR/vpn_refresher.py" 2>&1 | tail -5

echo "== 4) 注册 launchd 定时任务（每 10 分钟自动执行）"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tx.sync-kuaimao</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$DIR/refresh.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>StandardOutPath</key>
    <string>$DIR/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>$DIR/launchd.err.log</string>
</dict>
</plist>
PL
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "== 5) 完成。当前任务状态:"
launchctl list | grep sync-kuaimao && echo "  ✓ 本机守护进程已成功加载运行（开机后台静默自启）" || { echo "  [!] 任务加载失败"; exit 1; }
echo
echo "订阅地址 (固定不变)："
echo "  Clash:       https://gist.githubusercontent.com/1009476063/$GIST_ID/raw/vpn_subs_clash.txt"
echo "  QuantumultX: https://gist.githubusercontent.com/1009476063/$GIST_ID/raw/vpn_subs_qx.txt"
echo "实时日志：tail -f $DIR/refresh.log"
