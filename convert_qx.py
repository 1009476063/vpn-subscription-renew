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
        obfs = ''
        if tls:
            obfs = f'tls'
            if servername:
                obfs += f',host={servername}'
        
        params = []
        if skip_cert_verify:
            params.append('skip-cert-verify=1')
        if flow and 'xtls' in flow:
            params.append('xtls-params=xray')
        if obfs:
            params.append(obfs)
        
        param_str = ','.join(params)
        line = f'{name} = vless, {server}, {port}, {uuid}, {cipher}'
        if param_str:
            line += f', {param_str}'
        qx_lines.append(line)
    elif proxy_type == 'vmess':
        obfs = ''
        if tls:
            obfs = f'tls'
            if servername:
                obfs += f',host={servername}'
        
        params = []
        if skip_cert_verify:
            params.append('skip-cert-verify=1')
        if obfs:
            params.append(obfs)
        
        param_str = ','.join(params)
        line = f'{name} = vmess, {server}, {port}, {cipher}, {uuid}'
        if param_str:
            line += f', {param_str}'
        qx_lines.append(line)
    elif proxy_type == 'ss':
        method = proxy.get('cipher', 'aes-256-gcm')
        password = proxy.get('password', '')
        obfs = ''
        obfs_opts = proxy.get('plugin-opts', {})
        if proxy.get('plugin') == 'obfs':
            obfs = f'obfs={obfs_opts.get("mode", "http")}'
            if obfs_opts.get('host'):
                obfs += f',obfs-host={obfs_opts["host"]}'
        
        line = f'{name} = ss, {server}, {port}, encrypt-method={method}, password={password}'
        if obfs:
            line += f', {obfs}'
        qx_lines.append(line)
    elif proxy_type == 'trojan':
        obfs = f'tls'
        if servername:
            obfs += f',host={servername}'
        
        params = []
        if skip_cert_verify:
            params.append('skip-cert-verify=1')
        if obfs:
            params.append(obfs)
        
        param_str = ','.join(params)
        line = f'{name} = trojan, {server}, {port}, {uuid}'
        if param_str:
            line += f', {param_str}'
        qx_lines.append(line)

print('\n'.join(qx_lines))
