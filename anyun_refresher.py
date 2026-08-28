#!/usr/bin/env python3
"""
Anyun VPN 自动订阅刷新脚本
流程: 设备注册 → 获取节点列表 → 逐个获取 vless 链接
输出: Clash YAML + QuantumultX Base64 → 更新 Gist
"""

import base64
import os
import random
import sys
import time
import urllib.parse

import requests
import yaml

BASE_URL = "https://api.anyunvpn.com"
USER_AGENT = "evvpn/7 CFNetwork/1402.0.8 Darwin/22.2.0"
DEVICE_NAME = "iPhone13,4"
OS_VERSION = "16.2"
DEVICE_TYPE = "ios"

GIST_ID = os.environ.get("GIST_ID")
GIST_TOKEN = os.environ.get("GIST_TOKEN")
CLASH_FILENAME = "anyun_clash.txt"
QX_FILENAME = "anyun_qx.txt"


def generate_device_uid():
    return "".join(random.choice("0123456789abcdef") for _ in range(32))


def post_json(url, headers, payload=None, timeout=30):
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_anyun_links():
    """登录并获取所有节点的 vless 链接"""
    device_uid = generate_device_uid()
    login_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Host": "api.anyunvpn.com",
    }
    login_body = {
        "deviceName": DEVICE_NAME,
        "deviceUid": device_uid,
        "osVersion": OS_VERSION,
        "deviceType": DEVICE_TYPE,
    }
    login_resp = post_json(f"{BASE_URL}/api/user/auth/deviceLogin", login_headers, login_body)
    if login_resp.get("code") != 200 or not login_resp.get("data", {}).get("token"):
        raise RuntimeError(f"登录失败: {login_resp}")
    token = login_resp["data"]["token"]
    print(f"[SUCCESS] 登录成功 token: {token[:16]}...")

    node_headers = {
        "Accept": "application/json",
        "X-Token": token,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Host": "api.anyunvpn.com",
        "x-platform": "ios",
    }
    node_resp = post_json(f"{BASE_URL}/api/user/node/nodeList", node_headers, {})
    nodes = node_resp.get("data", {}).get("nodes") or []
    if not isinstance(nodes, list) or not nodes:
        raise RuntimeError(f"节点列表为空: {node_resp}")
    print(f"[SUCCESS] 获取到 {len(nodes)} 个节点")

    links = []
    for node in nodes:
        node_id = node.get("id")
        try:
            connect_resp = post_json(
                f"{BASE_URL}/api/user/node/connect", node_headers, {"nodeId": node_id}
            )
            node_links = connect_resp.get("data", {}).get("links") or []
            for link in node_links:
                if link.startswith("vless://") or link.startswith("vmess://"):
                    links.append(link)
        except Exception as e:
            print(f"[WARN] 节点 {node.get('nodeName')} (id={node_id}) 获取失败: {e}")
        time.sleep(0.2)

    if not links:
        raise RuntimeError("未获取到任何有效链接")
    print(f"[SUCCESS] 共获取 {len(links)} 条链接")
    return links


def parse_vless_uri(uri):
    """解析 vless:// 链接为 Clash proxy 字典"""
    parsed = urllib.parse.urlparse(uri)
    proxy = {
        "name": urllib.parse.unquote(parsed.fragment or "Anyun"),
        "type": "vless",
        "server": parsed.hostname,
        "port": parsed.port or 443,
        "uuid": parsed.username,
        "udp": True,
        "tls": True,
    }
    params = urllib.parse.parse_qs(parsed.query)
    if params.get("security", ["none"])[0] == "reality":
        proxy["servername"] = params.get("sni", [None])[0]
        proxy["client-fingerprint"] = params.get("fp", ["chrome"])[0]
        proxy["reality-opts"] = {
            "public-key": params.get("pbk", [""])[0],
            "short-id": params.get("sid", [""])[0],
        }
    if params.get("flow"):
        proxy["flow"] = params["flow"][0]
    return proxy


def build_clash_yaml(links):
    proxies = []
    for link in links:
        if link.startswith("vless://"):
            proxies.append(parse_vless_uri(link))
        elif link.startswith("vmess://"):
            payload = base64.b64decode(link[len("vmess://"):] + "==").decode("utf-8", "ignore")
            vmess = json_loads(payload)
            proxies.append(
                {
                    "name": vmess.get("ps", "Anyun"),
                    "type": "vmess",
                    "server": vmess.get("add"),
                    "port": int(vmess.get("port", 443)),
                    "uuid": vmess.get("id"),
                    "alterId": int(vmess.get("aid", 0)),
                    "cipher": vmess.get("scy", "auto"),
                    "tls": bool(vmess.get("tls")),
                    "network": vmess.get("net", "tcp"),
                    "ws-opts": {"path": vmess.get("path") or "/", "headers": {"Host": vmess.get("host") or ""}},
                }
            )

    names = [p["name"] for p in proxies]
    config = {
        "mixed-port": 7890,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "dns": {
            "enable": True,
            "enhanced-mode": "fake-ip",
            "nameserver": ["https://doh.pub/dns-query", "https://dns.alidns.com/dns-query"],
        },
        "proxies": proxies,
        "proxy-groups": [
            {"name": "节点选择", "type": "select", "proxies": ["自动选择"] + names},
            {"name": "自动选择", "type": "url-test", "url": "http://www.gstatic.com/generate_204", "interval": 300, "proxies": names},
        ],
        "rules": ["MATCH,节点选择"],
    }
    return yaml.safe_dump(config, allow_unicode=True, sort_keys=False)


def json_loads(s):
    import json
    return json.loads(s)


def build_qx_base64(links):
    """QuantumultX 使用 Base64 编码的 URI 列表"""
    lines = []
    for link in links:
        if link.startswith("vless://"):
            parsed = urllib.parse.urlparse(link)
            name = urllib.parse.unquote(parsed.fragment or "Anyun")
            params = urllib.parse.parse_qs(parsed.query)
            qs = {
                "encryption": "none",
                "security": "reality",
                "sni": params.get("sni", [""])[0],
                "pbk": params.get("pbk", [""])[0],
                "sid": params.get("sid", [""])[0],
                "fp": params.get("fp", ["chrome"])[0],
                "type": "tcp",
            }
            if params.get("flow"):
                qs["flow"] = params["flow"][0]
            query = urllib.parse.urlencode(qs)
            uri = f"vless://{parsed.username}@{parsed.hostname}:{parsed.port}?{query}#{urllib.parse.quote(name)}"
            lines.append(uri)
        elif link.startswith("vmess://"):
            lines.append(link)
    return base64.b64encode("\n".join(lines).encode()).decode()


def update_gist(clash_yaml, qx_b64):
    if not GIST_TOKEN or not GIST_ID:
        print("[ERROR] GIST_TOKEN 或 GIST_ID 未设置")
        return False
    headers = {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"files": {CLASH_FILENAME: {"content": clash_yaml}, QX_FILENAME: {"content": qx_b64}}}
    resp = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=data, timeout=30)
    resp.raise_for_status()
    print("[SUCCESS] Gist 更新成功")
    return True


def main():
    print("--- Anyun VPN Refresher ---")
    try:
        links = fetch_anyun_links()
    except Exception as e:
        print(f"[FAILED] 获取节点失败: {e}")
        sys.exit(1)

    clash_yaml = build_clash_yaml(links)
    qx_b64 = build_qx_base64(links)
    print(f"[INFO] Clash {len(links)} 节点, QX Base64 生成完成")

    if update_gist(clash_yaml, qx_b64):
        print("[DONE] Anyun 订阅刷新成功")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
