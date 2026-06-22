#!/usr/bin/env python3
"""
快猫VPN 自动订阅续订脚本
获取订阅 → 解析为 Clash 和 QuantumultX 格式 → 更新 Gist
"""

import random
import os
import sys
import json
import base64
import urllib.parse
import requests
import yaml

# --- 配置 ---
API_URL = "https://api.kuaimiaov4.com/appV4api/manusAi/applyLogin"
GIST_ID = os.environ.get('GIST_ID')
GIST_TOKEN = os.environ.get('GIST_TOKEN')
GIST_FILENAME_CLASH = "vpn_subs_clash.txt"
GIST_FILENAME_QX = "vpn_subs_qx.txt"

# 增加超时时间和重试机制
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def generate_device_key():
    """生成随机设备密钥"""
    return f"{random.randint(10000000, 99999999)}-f3ca-4bdf-9192-f5c452a2c923"


def request_with_retry(method, url, max_retries=MAX_RETRIES, timeout=REQUEST_TIMEOUT, **kwargs):
    """带重试的请求函数"""
    for attempt in range(max_retries):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=timeout, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, timeout=timeout, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            print(f"[WARN] Request timeout (attempt {attempt + 1}/{max_retries}): {url}")
            if attempt < max_retries - 1:
                import time
                wait = (attempt + 1) * 5
                print(f"[INFO] Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.ConnectionError as e:
            print(f"[WARN] Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                wait = (attempt + 1) * 5
                print(f"[INFO] Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise
    return None


def get_subscription():
    """获取订阅链接内容"""
    device_key = generate_device_key()
    
    headers = {
        "user-agent": "Dart/3.12 (dart:io)",
        "content-type": "application/json",
        "accept-encoding": "gzip"
    }
    
    try:
        # 第一步：获取订阅URL
        response = request_with_retry('POST', API_URL, json={"deviceKey": device_key}, headers=headers)
        data = response.json()
        
        yml_url = data.get('data', {}).get('ymlUrl')
        if not yml_url:
            print(f"[ERROR] No ymlUrl in response: {data}")
            return None
        
        print(f"[SUCCESS] Got subscription URL: {yml_url}")
        
        # 第二步：获取实际订阅内容（增加超时）
        sub_response = request_with_retry('GET', yml_url, timeout=60)
        print(f"[SUCCESS] Got subscription content ({len(sub_response.text)} bytes)")
        return sub_response.text
        
    except Exception as e:
        print(f"[ERROR] Failed to get subscription: {e}")
        return None


def clash_to_quantumultx(clash_content):
    """将 Clash YAML 格式转换为 QuantumultX URI 格式"""
    data = yaml.safe_load(clash_content)
    qx_lines = []
    
    for proxy in data.get('proxies', []):
        name = proxy.get('name', '')
        server = proxy.get('server', '')
        port = proxy.get('port', 0)
        proxy_type = proxy.get('type', '')
        uuid = proxy.get('uuid', '')
        cipher = proxy.get('cipher', 'auto')
        tls = proxy.get('tls', False)
        skip_cert_verify = proxy.get('skip-cert-verify', False)
        servername = proxy.get('servername', '')
        flow = proxy.get('flow', '')
        fingerprint = proxy.get('client-fingerprint', '')
        
        # Reality 参数
        reality_opts = proxy.get('reality-opts', {})
        public_key = reality_opts.get('public-key', '')
        short_id = reality_opts.get('short-id', '')
        
        if proxy_type == 'vless':
            params = ["encryption=none"]
            
            if public_key:
                # Reality 协议
                params.append("security=reality")
                if servername:
                    params.append(f"sni={servername}")
                params.append(f"pbk={public_key}")
                if short_id:
                    params.append(f"sid={short_id}")
                if fingerprint:
                    params.append(f"fp={fingerprint}")
                params.append("allowInsecure=0")
            elif tls:
                # 普通 TLS
                params.append("security=tls")
                if servername:
                    params.append(f"sni={servername}")
                params.append("allowInsecure=0" if not skip_cert_verify else "allowInsecure=1")
            
            if flow and 'xtls' in flow:
                params.append("flow=xtls-rprx-vision")
            
            params.append("type=tcp")
            
            param_str = "&".join(params)
            encoded_name = urllib.parse.quote(name)
            uri = f"vless://{uuid}@{server}:{port}?{param_str}#{encoded_name}"
            qx_lines.append(uri)
            
        elif proxy_type == 'vmess':
            vmess_config = {
                "v": "2", "ps": name, "add": server, "port": str(port),
                "id": uuid, "aid": str(proxy.get('alterId', 0)),
                "scy": cipher or "auto", "net": proxy.get('network', 'tcp'),
                "type": "none", "host": "", "path": "",
                "tls": "tls" if tls else "", "sni": servername,
                "alpn": "", "fp": fingerprint
            }
            vmess_json = json.dumps(vmess_config)
            vmess_b64 = base64.b64encode(vmess_json.encode()).decode()
            qx_lines.append(f"vmess://{vmess_b64}")
            
        elif proxy_type == 'trojan':
            params = []
            if tls:
                params.append("security=tls")
                if servername:
                    params.append(f"sni={servername}")
                params.append("allowInsecure=0" if not skip_cert_verify else "allowInsecure=1")
            param_str = "&".join(params) if params else ""
            encoded_name = urllib.parse.quote(name)
            uri = f"trojan://{uuid}@{server}:{port}"
            if param_str:
                uri += f"?{param_str}"
            uri += f"#{encoded_name}"
            qx_lines.append(uri)
            
        elif proxy_type == 'ss':
            method_pwd = base64.b64encode(f"{cipher}:{proxy.get('password', '')}".encode()).decode()
            encoded_name = urllib.parse.quote(name)
            qx_lines.append(f"ss://{method_pwd}@{server}:{port}#{encoded_name}")
    
    return base64.b64encode("\n".join(qx_lines).encode()).decode()


def update_gist(clash_content, qx_base64):
    """更新 Gist"""
    if not GIST_TOKEN or not GIST_ID:
        print("[ERROR] GIST_TOKEN or GIST_ID not set.")
        return False
    
    headers = {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "files": {
            GIST_FILENAME_CLASH: {"content": clash_content},
            GIST_FILENAME_QX: {"content": qx_base64}
        }
    }
    
    try:
        response = requests.patch(f"https://api.github.com/gists/{GIST_ID}",
                                    headers=headers, json=data, timeout=30)
        print("[SUCCESS] Gist updated successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update Gist: {e}")
        return False


def main():
    """主函数"""
    print("--- Starting VPN Subscription Refresher ---")
    
    # 获取订阅
    clash_content = get_subscription()
    if not clash_content:
        print("[FAILED] Could not get subscription content.")
        sys.exit(1)
    
    # 转换为 QuantumultX 格式
    print("[INFO] Converting to QuantumultX format...")
    qx_base64 = clash_to_quantumultx(clash_content)
    
    # 更新 Gist
    if update_gist(clash_content, qx_base64):
        print("[DONE] Subscription refreshed successfully!")
    else:
        print("[FAILED] Could not update Gist.")
        sys.exit(1)


if __name__ == "__main__":
    main()
