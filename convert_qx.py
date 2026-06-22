import sys
import yaml
import base64

content = sys.stdin.read()
data = yaml.safe_load(content)

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
    
    # Build vless URI format
    if proxy_type == 'vless':
        # vless://uuid@server:port?encryption=none&security=tls&sni=servername&flow=xtls-rprx-vision&type=tcp#Tag
        params = []
        params.append("encryption=none")
        
        if tls:
            params.append("security=tls")
            if servername:
                params.append(f"sni={servername}")
            if not skip_cert_verify:
                params.append("allowInsecure=0")
            else:
                params.append("allowInsecure=1")
        
        if flow and 'xtls' in flow:
            params.append("flow=xtls-rprx-vision")
        
        params.append("type=tcp")
        
        param_str = "&".join(params)
        # URL encode the name for tag
        import urllib.parse
        encoded_name = urllib.parse.quote(name)
        
        uri = f"vless://{uuid}@{server}:{port}?{param_str}#{encoded_name}"
        qx_lines.append(uri)
    elif proxy_type == 'vmess':
        # Build vmess config for QuantumultX
        vmess_config = {
            "v": "2",
            "ps": name,
            "add": server,
            "port": str(port),
            "id": uuid,
            "aid": str(proxy.get('alterId', 0)),
            "scy": cipher if cipher else "auto",
            "net": proxy.get('network', 'tcp'),
            "type": "none",
            "host": "",
            "path": "",
            "tls": "tls" if tls else "",
            "sni": servername,
            "alpn": "",
            "fp": ""
        }
        
        # Handle ws options
        if proxy.get('network') == 'ws':
            ws_opts = proxy.get('ws-opts', {})
            vmess_config["host"] = ws_opts.get('headers', {}).get('Host', '')
            vmess_config["path"] = ws_opts.get('path', '')
        
        # Base64 encode
        vmess_json = str(vmess_config).replace("'", '"')
        vmess_b64 = base64.b64encode(vmess_json.encode()).decode()
        uri = f"vmess://{vmess_b64}"
        qx_lines.append(uri)
    elif proxy_type == 'trojan':
        # trojan://password@server:port?security=tls&sni=servername#Tag
        params = []
        if tls:
            params.append("security=tls")
            if servername:
                params.append(f"sni={servername}")
            if not skip_cert_verify:
                params.append("allowInsecure=0")
            else:
                params.append("allowInsecure=1")
        
        param_str = "&".join(params) if params else ""
        import urllib.parse
        encoded_name = urllib.parse.quote(name)
        
        uri = f"trojan://{uuid}@{server}:{port}"
        if param_str:
            uri += f"?{param_str}"
        uri += f"#{encoded_name}"
        qx_lines.append(uri)
    elif proxy_type == 'ss':
        # ss://base64(method:password)@server:port#Tag
        import urllib.parse
        method_pwd = base64.b64encode(f"{cipher}:{proxy.get('password', '')}".encode()).decode()
        encoded_name = urllib.parse.quote(name)
        uri = f"ss://{method_pwd}@{server}:{port}#{encoded_name}"
        qx_lines.append(uri)

# Output as base64 encoded subscription
output = "\n".join(qx_lines)
print(base64.b64encode(output.encode()).decode())
