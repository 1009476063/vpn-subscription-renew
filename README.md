# 快猫VPN 自动续订服务

## 📋 项目简介

本项目利用 GitHub Actions 实现快猫VPN订阅链接的自动续订。订阅每30分钟自动更新，确保链接永不过期。

## 🔗 订阅链接

| 客户端 | 订阅地址 |
|--------|----------|
| **Clash** | https://raw.githubusercontent.com/1009476063/vpn-subscription-renew/main/vpn_subs_clash.txt |
| **QuantumultX** | https://raw.githubusercontent.com/1009476063/vpn-subscription-renew/main/vpn_subs_qx.txt |

### QuantumultX 使用方法

在订阅链接后添加资源解析器参数：

```
https://raw.githubusercontent.com/1009476063/vpn-subscription-renew/main/vpn_subs_qx.txt?opt-parser=true&resource_parser=url
```

## ⚙️ 工作原理

1. GitHub Actions 每 **25分钟** 自动运行一次
2. 调用快猫VPN API获取新的30分钟订阅
3. 解析 Clash YAML 格式并转换为 QuantumultX URI 格式
4. 提交更新到仓库，订阅链接自动刷新

## 📁 文件结构

```
├── .github/workflows/
│   └── renew.yml          # GitHub Actions 工作流
├── convert_qx.py          # Clash → QuantumultX 格式转换脚本
├── vpn_subs_clash.txt     # Clash 格式订阅（自动生成）
└── vpn_subs_qx.txt        # QuantumultX 格式订阅（自动生成）
```

## 🔧 技术细节

- **协议支持**: VLESS (Reality/TLS), VMess, Trojan, Shadowsocks
- **Reality 参数**: 自动提取 `public-key`, `short-id`, `fingerprint`
- **格式转换**: 使用 Python + PyYAML 解析 Clash 配置

## ⚠️ 注意事项

- 订阅链接每25分钟自动更新，无需手动操作
- 节点信息由快猫VPN提供，本项目仅做格式转换和托管
- 如遇问题请检查 GitHub Actions 运行日志

## 📄 License

MIT
