import sys
import yaml
import base64
import urllib.parse

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
    fingerprint = proxy.get('client-fingerprint', '')
    
    # Reality params
    reality_opts = proxy.get('reality-opts', {})
    public_key = reality_opts.get('public-key', '')
    short_id = reality_opts.get('short-id', '')
    
    if proxy_type == 'vless':
        params = []
        params.append("encryption=none")
        
        # Check if Reality
        if public_key:
            params.append("security=reality")
            if servername:
                params.append(f"sni={servername}")
            if public_key:
                params.append(f"pbk={public_key}")
            if short_id:
                params.append(f"sid={short_id}")
            if fingerprint:
                params.append(f"fp={fingerprint}")
            if skip_cert_verify:
                params.append("allowInsecure=1")
            else:
                params.append("allowInsecure=0")
        elif tls:
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
        encoded_name = urllib.parse.quote(name)
        
        uri = f"vless://{uuid}@{server}:{port}?{param_str}#{encoded_name}"
        qx_lines.append(uri)
    elif proxy_type == 'vmess':
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
            "fp": fingerprint
        }
        
        if proxy.get('network') == 'ws':
            ws_opts = proxy.get('ws-opts', {})
            vmess_config["host"] = ws_opts.get('headers', {}).get('Host', '')
            vmess_config["path"] = ws_opts.get('path', '')
        
        vmess_json = str(vmess_config).replace("'", '"')
        vmess_b64 = base64.b64encode(vmess_json.encode()).decode()
        uri = f"vmess://{vmess_b64}"
        qx_lines.append(uri)
    elif proxy_type == 'trojan':
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
        encoded_name = urllib.parse.quote(name)
        
        uri = f"trojan://{uuid}@{server}:{port}"
        if param_str:
            uri += f"?{param_str}"
        uri += f"#{encoded_name}"
        qx_lines.append(uri)
    elif proxy_type == 'ss':
        method_pwd = base64.b64encode(f"{cipher}:{proxy.get('password', '')}".encode()).decode()
        encoded_name = urllib.parse.quote(name)
        uri = f"ss://{method_pwd}@{server}:{port}#{encoded_name}"
        qx_lines.append(uri)

output = "\n".join(qx_lines)
print(base64.b64encode(output.encode()).decode())
