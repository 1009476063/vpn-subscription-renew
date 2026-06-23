# 快猫VPN 自动续订服务

## 📋 项目简介

利用 GitHub Actions 实现快猫VPN订阅的**无感永续**。通过链式自触发机制，每25分钟自动获取新订阅并更新 Gist，确保30分钟过期的订阅链接始终有效。

## 🔗 订阅链接

| 客户端 | 订阅地址 |
|--------|----------|
| **Clash** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/vpn_subs_clash.txt` |
| **QuantumultX** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/vpn_subs_qx.txt?opt-parser=true&resource_parser=url` |

### 客户端配置建议

- **刷新间隔**：设置为 **25分钟或更短**，确保在过期前获取新订阅
- 订阅链接固定不变，客户端定时刷新即可

## ⚙️ 工作原理

```
┌─────────────┐     repository_dispatch     ┌──────────────┐
│ trigger.yml │ ──────────────────────────→ │  renew.yml   │
│  (cron备用)  │                             │  (主工作流)   │
└─────────────┘                             └──────┬───────┘
                                                   │
                                        ┌──────────▼──────────┐
                                        │ 1. 获取新订阅        │
                                        │ 2. 解析为 Clash 格式  │
                                        │ 3. 转换为 QX 格式     │
                                        │ 4. 更新 Gist         │
                                        │ 5. sleep 25 分钟     │
                                        │ 6. 触发下一次 renew   │
                                        └──────────┬──────────┘
                                                   │
                                          repository_dispatch
                                                   │
                                        ┌──────────▼──────────┐
                                        │    无限循环 🔄        │
                                        └─────────────────────┘
```

1. **链式自触发**：`renew.yml` 成功更新后，等待25分钟自动触发下一次运行，形成永续循环
2. **冷启动兜底**：`trigger.yml` 通过 cron 定时触发，作为链断后的恢复机制
3. 每次运行调用快猫VPN API获取新订阅，解析并更新到公开 Gist

## 📁 文件结构

```
├── .github/workflows/
│   ├── renew.yml          # 主工作流：获取订阅 + 链式自触发
│   └── trigger.yml        # 备用触发器：cron 调度启动
├── vpn_refresher.py       # 核心脚本：API调用 + 格式转换 + Gist更新
├── vpn_subs_clash.txt     # Clash 格式订阅（本地副本）
└── vpn_subs_qx.txt        # QuantumultX 格式订阅（本地副本）
```

## 🔧 技术细节

- **协议支持**: VLESS (Reality/TLS), VMess, Trojan, Shadowsocks
- **Reality 参数**: 自动提取 `public-key`, `short-id`, `client-fingerprint`
- **格式转换**: Python + PyYAML 解析 Clash YAML → QuantumultX URI（Base64 编码）
- **容错机制**: HTTP 请求自动重试（3次），超时时间 60 秒

## ⚠️ 注意事项

- 订阅链接固定不变，客户端只需设置 ≤25分钟的自动刷新间隔
- 节点信息由快猫VPN提供，本项目仅做格式转换和托管
- GitHub Actions 运行日志可在 [Actions 页面](https://github.com/1009476063/vpn-subscription-renew/actions) 查看
- 如链式循环中断，cron 备用触发器会自动恢复
