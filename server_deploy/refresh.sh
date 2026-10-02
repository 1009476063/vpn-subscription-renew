#!/bin/sh
# 快猫订阅双机协同永续管道（Linux 常驻服务器智能守护与应急兜底）
# 1. 优先校验 Gist 新鲜度：若 Mac 本地已在有效周期内（<20分钟）刷新，确认健康并直接上报 Uptime Kuma UP，避免重复刷频被上游风控；
# 2. 关机/失联兜底：若 Gist 超过 20 分钟未更新（判定 Mac 关机或失联），自动激活 VPS 本地 WARP 隧道执行应急续订推送到 Gist；
# 3. 杜绝误报：只有在 Mac 失联且 VPS 兜底亦失败时才上报 DOWN。

DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/refresh.log"
TS=$(date "+%Y-%m-%d %H:%M:%S")
PUSH_URL="http://129.146.99.81:8068/api/push/km_renew_push_129146252112_sync"

# 随机扰动 3~15 秒（外部手动执行时可通过传入 nojitter 跳过）
if [ "$1" != "nojitter" ]; then
    JITTER=$(( (RANDOM % 13) + 3 ))
    sleep "$JITTER"
fi

if [ -f "$DIR/.env" ]; then
    . "$DIR/.env"
fi

if [ -z "$GIST_TOKEN" ] || [ -z "$GIST_ID" ]; then
    echo "$TS [ERROR] GIST_TOKEN or GIST_ID not configured" >> "$LOG"
    curl --noproxy "*" -s -m 5 "${PUSH_URL}?status=down&msg=missing_env" >/dev/null 2>&1 || true
    exit 1
fi

cd "$DIR" || exit 1
export GIST_TOKEN GIST_ID

# 查询 Gist 最近一次更新距今秒数 (AGE_SECONDS)
GIST_AGE=$(python3 -c "
import requests, os, datetime
token = os.environ.get('GIST_TOKEN', '')
gist_id = os.environ.get('GIST_ID', '')
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'} if token else {}
try:
    r = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers, timeout=10)
    data = r.json()
    updated_at_str = data.get('updated_at', '')
    if updated_at_str:
        updated_at = datetime.datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
        now = datetime.datetime.now(datetime.timezone.utc)
        print(int((now - updated_at).total_seconds()))
    else:
        print(-1)
except Exception:
    print(-1)
" 2>/dev/null)

# 快猫单次订阅有效时长为 30 分钟 (1800 秒)
# 若 Gist 在 20 分钟 (1200 秒) 内已被 Mac 主机刷新，说明订阅池极度健康
if [ "$GIST_AGE" -ge 0 ] 2>/dev/null && [ "$GIST_AGE" -lt 1200 ] 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [HEALTHY] Gist fresh (age=${GIST_AGE}s < 1200s), active by Mac. Skip redundant upstream fetch." >> "$LOG"
    curl --noproxy "*" -s -m 8 "${PUSH_URL}?status=up&msg=Gist_fresh_active&ping=${GIST_AGE}" >/dev/null 2>&1 || true
    exit 0
fi

# 若 Gist 超过 20 分钟未更新或查询异常，判定 Mac 关机/失联，启动 VPS 应急兜底
echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] Gist age=${GIST_AGE}s >= 1200s. Mac may be off. Activating VPS fallback renewal..." >> "$LOG"

check_proxy() {
    curl -s -m 5 --socks5-hostname 127.0.0.1:40000 https://cloudflare.com/cdn-cgi/trace >/dev/null 2>&1
}

restart_wireproxy() {
    rc-service wireproxy stop >/dev/null 2>&1 || systemctl restart wireproxy >/dev/null 2>&1 || true
    killall -9 wireproxy >/dev/null 2>&1 || true
    sleep 1
    rc-service wireproxy zap >/dev/null 2>&1 || true
    rc-service wireproxy start >/dev/null 2>&1 || true
    sleep 2
}

if ! check_proxy; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] SOCKS5 proxy unhealthy, restarting wireproxy..." >> "$LOG"
    restart_wireproxy
fi

export HTTP_PROXY="socks5h://127.0.0.1:40000"
export HTTPS_PROXY="socks5h://127.0.0.1:40000"
export ALL_PROXY="socks5h://127.0.0.1:40000"
export http_proxy="socks5h://127.0.0.1:40000"
export https_proxy="socks5h://127.0.0.1:40000"
export all_proxy="socks5h://127.0.0.1:40000"
export NO_PROXY="129.146.99.81,127.0.0.1,localhost,api.github.com"
export no_proxy="129.146.99.81,127.0.0.1,localhost,api.github.com"

python3 "$DIR/vpn_refresher.py" >> "$LOG" 2>&1
RC=$?

if [ $RC -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] First attempt failed (rc=$RC), checking proxy and retrying in 15s..." >> "$LOG"
    if ! check_proxy; then
        restart_wireproxy
    fi
    sleep 15
    python3 "$DIR/vpn_refresher.py" >> "$LOG" 2>&1
    RC=$?
fi

if [ $RC -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DONE] VPS fallback renewal success (done_count: $(grep -c DONE "$LOG" 2>/dev/null))" >> "$LOG"
    curl --noproxy "*" -s -m 8 "${PUSH_URL}?status=up&msg=VPS_fallback_OK&ping=${GIST_AGE}" >/dev/null 2>&1 || true
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] VPS fallback renewal failed (rc=$RC)" >> "$LOG"
    curl --noproxy "*" -s -m 8 "${PUSH_URL}?status=down&msg=refresh_failed_rc_${RC}" >/dev/null 2>&1 || true
fi

# 日志滚动防爆盘：超过 5000 行保留最近 3000 行
if [ -f "$LOG" ] && [ $(wc -l < "$LOG") -gt 5000 ]; then
    tail -n 3000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

exit $RC
