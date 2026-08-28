#!/usr/bin/env python3
"""
红盾（Red Shield）VPN 自动订阅刷新脚本
流程: 设备注册(带 MD5 签名) → 获取节点列表 → 生成 ss 链接
输出: Clash YAML + QuantumultX Base64 → 更新 Gist
"""

import base64
import hashlib
import os
import random
import sys
import time
import urllib.parse

import requests
import yaml

SALT = "NjNXNzA4SXcyOXBsazRCQ0g1MW4="
HOST = "http://207.148.33.174"
UA_TEMPLATE = (
    "pt=IOS,version=1.0.3,verId=10,system=16.2,bundleId=com.red.shield,"
    "deviceId={device},lang=zh-Hans-US,brand=Apple,model=iPhone13-4,net=4G;"
)

GIST_ID = os.environ.get("GIST_ID")
GIST_TOKEN = os.environ.get("GIST_TOKEN")
CLASH_FILENAME = "hongdun_clash.txt"
QX_FILENAME = "hongdun_qx.txt"


def new_device_id():
    chars = "0123456789ABCDEF"
    s = []
    for i in range(36):
        c = "-" if i in (8, 13, 18, 23) else random.choice(chars)
        s.append(c)
    return "".join(s)


def sign(params, ts):
    s = ""
    for k in sorted(params.keys()):
        s += "{%s}{%s}" % (k, str(params[k]))
    s += SALT + str(ts)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def build_request(path, params, token=None, uid=None):
    ts = str(int(time.time()))
    all_params = dict(params)
    if token:
        all_params["token"] = token
    if uid:
        all_params["uid"] = uid
    sign_val = sign(all_params, ts)
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "207.148.33.174",
        "User-Agent": UA_TEMPLATE.format(device=params["deviceId"]),
        "Accept-Language": "zh-Hans-US;q=1, en-GB;q=0.9, en-US;q=0.8, zh-Hant-US;q=0.7",
        "SIGN": sign_val,
        "TIMESTAMP": ts,
    }
    body_parts = []
    for k, v in all_params.items():
        if v is not None:
            body_parts.append(f"{k}={urllib.parse.quote(str(v))}")
    return {"url": HOST + path, "headers": headers, "body": "&".join(body_parts)}


def post_form(req, timeout=30):
    resp = requests.post(req["url"], data=req["body"], headers=req["headers"], timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_hongdun_links():
    """登录并返回 ss:// 链接列表"""
    device = new_device_id()
    base_params = {
        "bundleId": "com.red.shield",
        "channel": "10000",
        "deviceId": device,
        "lang": "zh-CN",
        "platform": "2",
        "ver": "3",
    }

    login_req = build_request("/api/user.loginByDeviceId", base_params)
    login_resp = post_form(login_req)
    if login_resp.get("response_status", {}).get("code") != 0:
        raise RuntimeError(f"登录失败: {login_resp}")
    token = login_resp.get("response_data", {}).get("token")
    uid = login_resp.get("response_data", {}).get("userinfo", {}).get("uid")
    if not token or not uid:
        raise RuntimeError(f"未获取到 token/uid: {login_resp}")
    print(f"[SUCCESS] 登录成功 uid={uid}")

    node_req = build_request("/api/node.getNodeList", base_params, token, uid)
    node_resp = post_form(node_req)
    nodes = node_resp.get("response_data")
    if not isinstance(nodes, list) or not nodes:
        raise RuntimeError(f"节点列表为空: {node_resp}")
    print(f"[SUCCESS] 获取到 {len(nodes)} 个节点")

    links = []
    for node in nodes:
        name = node.get("name") or f"{node.get('country')}-{node.get('city')}"
        method = node.get("method") or "aes-256-cfb"
        pwd = node.get("password")
        ip = node.get("ip")
        port = node.get("port")
        if not pwd or not ip or not port:
            continue
        userinfo = base64.b64encode(f"{method}:{pwd}".encode()).decode()
        links.append(f"ss://{userinfo}@{ip}:{port}#{urllib.parse.quote(name)}")

    if not links:
        raise RuntimeError("未生成任何 ss 链接")
    print(f"[SUCCESS] 共生成 {len(links)} 条 ss 链接")
    return links


def parse_ss_uri(uri):
    parsed = urllib.parse.urlparse(uri)
    name = urllib.parse.unquote(parsed.fragment or "红盾")
    userinfo = base64.b64decode(parsed.username.encode() + b"==").decode("utf-8", "ignore")
    method, _, pwd = userinfo.partition(":")
    return {
        "name": name,
        "type": "ss",
        "server": parsed.hostname,
        "port": parsed.port,
        "cipher": method,
        "password": pwd,
    }


def build_clash_yaml(links):
    proxies = [parse_ss_uri(link) for link in links]
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


def build_qx_base64(links):
    return base64.b64encode("\n".join(links).encode()).decode()


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
    print("--- 红盾 VPN Refresher ---")
    try:
        links = fetch_hongdun_links()
    except Exception as e:
        print(f"[FAILED] 获取节点失败: {e}")
        sys.exit(1)

    clash_yaml = build_clash_yaml(links)
    qx_b64 = build_qx_base64(links)
    print(f"[INFO] Clash {len(links)} 节点, QX Base64 生成完成")

    if update_gist(clash_yaml, qx_b64):
        print("[DONE] 红盾订阅刷新成功")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
