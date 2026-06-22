import sys
import yaml

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
    
    if proxy_type == 'vless':
        # QuantumultX vless format
        obfs_params = []
        if tls:
            obfs_params.append('over-tls=true')
            if servername:
                obfs_params.append(f'tls-host={servername}')
            obfs_params.append('tls-verification=true' if not skip_cert_verify else 'tls-verification=false')
        if flow and 'xtls' in flow:
            obfs_params.append('tls-params=xtls')
        
        obfs_str = ', '.join(obfs_params)
        line = f'{name} = vless, {server}, {port}, {uuid}, {cipher}'
        if obfs_str:
            line += f', {obfs_str}'
        qx_lines.append(line)
    elif proxy_type == 'vmess':
        # QuantumultX vmess format
        obfs_params = []
        if tls:
            obfs_params.append('over-tls=true')
            if servername:
                obfs_params.append(f'tls-host={servername}')
            obfs_params.append('tls-verification=true' if not skip_cert_verify else 'tls-verification=false')
        if proxy.get('network') == 'ws':
            obfs_params.append('obfs=ws')
            obfs_path = proxy.get('ws-opts', {}).get('path', '')
            if obfs_path:
                obfs_params.append(f'obfs-uri={obfs_path}')
        
        obfs_str = ', '.join(obfs_params)
        line = f'{name} = vmess, {server}, {port}, {cipher}, {uuid}'
        if obfs_str:
            line += f', {obfs_str}'
        qx_lines.append(line)
    elif proxy_type == 'ss':
        method = proxy.get('cipher', 'aes-256-gcm')
        password = proxy.get('password', '')
        obfs_params = []
        plugin = proxy.get('plugin', '')
        plugin_opts = proxy.get('plugin-opts', {})
        if plugin == 'obfs':
            obfs_params.append(f'obfs={plugin_opts.get("mode", "http")}')
            if plugin_opts.get('host'):
                obfs_params.append(f'obfs-host={plugin_opts["host"]}')
        
        obfs_str = ', '.join(obfs_params)
        line = f'{name} = ss, {server}, {port}, encrypt-method={method}, password={password}'
        if obfs_str:
            line += f', {obfs_str}'
        qx_lines.append(line)
    elif proxy_type == 'trojan':
        obfs_params = []
        obfs_params.append('over-tls=true')
        if servername:
            obfs_params.append(f'tls-host={servername}')
        obfs_params.append('tls-verification=true' if not skip_cert_verify else 'tls-verification=false')
        
        obfs_str = ', '.join(obfs_params)
        line = f'{name} = trojan, {server}, {port}, {uuid}'
        if obfs_str:
            line += f', {obfs_str}'
        qx_lines.append(line)

print('\n'.join(qx_lines))
