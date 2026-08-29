# VPN 自动续订服务

## 📋 项目简介

利用 GitHub Actions 实现多源 VPN 订阅的**自动续订**。通过链式自触发机制定时获取新订阅并更新 Gist，确保订阅链接始终有效。

## 🔗 订阅链接

### 快猫VPN（每 25 分钟刷新）

| 客户端 | 订阅地址 |
|--------|----------|
| **Clash** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/vpn_subs_clash.txt` |
| **QuantumultX** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/vpn_subs_qx.txt?opt-parser=true&resource_parser=url` |

> 快猫实际为**约每 15 分钟**刷新一轮（14 分钟链式间隔 + 双平台容错），保证在 30 分钟 UUID 过期前完成替换。

### Anyun VPN（每 15 分钟刷新）

| 客户端 | 订阅地址 |
|--------|----------|
| **Clash** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/anyun_clash.txt` |
| **QuantumultX** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/anyun_qx.txt?opt-parser=true&resource_parser=url` |

### 红盾 VPN（每 15 分钟刷新）

| 客户端 | 订阅地址 |
|--------|----------|
| **Clash** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/hongdun_clash.txt` |
| **QuantumultX** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/hongdun_qx.txt?opt-parser=true&resource_parser=url` |

### QuantumultX 使用方法

在订阅链接后添加资源解析器参数（KOP-XIAO 资源解析器）：

`?opt-parser=true&resource_parser=url`

### 客户端配置建议

- 快猫：刷新间隔设为 **10 分钟或更短**（UUID 30 分钟过期，双保险）
- Anyun / 红盾：刷新间隔设为 **15 分钟或更短**
- 订阅链接固定不变，客户端定时刷新即可

## ⚙️ 工作原理

1. **链式自触发**：主工作流成功更新后，等待 14 分钟自动触发下一次运行，形成连续循环
2. **双平台容错**：快猫主链路跑 Ubuntu，失败时自动切到 macOS 备份链路（上游对部分 Actions 出口 IP 段返回 403，双平台显著提高成功率）
3. **冷启动兜底**：trigger 工作流通过 cron（每 15 分钟）定时触发，作为链断后的恢复机制
4. 每次运行调用各 VPN API 获取新订阅，解析为 Clash YAML 与 QuantumultX Base64，更新到公开 Gist

快猫链路约每 15 分钟刷新一次；Anyun 与红盾链路每 15 分钟刷新一次。

## 📁 文件结构

```
├── .github/workflows/
│   ├── renew.yml                     # 快猫主工作流：获取订阅 + 链式自触发
│   ├── trigger.yml                   # 快猫备用触发器：cron 调度启动
│   ├── renew_anyun_hongdun.yml       # Anyun/红盾主工作流：15分钟链式自触发
│   └── trigger_anyun_hongdun.yml     # Anyun/红盾备用触发器：cron 调度启动
├── vpn_refresher.py       # 快猫核心脚本：API调用 + 格式转换 + Gist更新
├── anyun_refresher.py    # Anyun核心脚本：vless节点获取 + 格式转换
├── hongdun_refresher.py  # 红盾核心脚本：ss节点获取 + 格式转换
├── Anyun.js              # Anyun 原始参考脚本
└── hongdun.js            # 红盾 原始参考脚本
```

## 🔧 技术细节

- **协议支持**: VLESS (Reality/TLS), VMess, Trojan, Shadowsocks
- **Reality 参数**: 自动提取 `public-key`, `short-id`, `client-fingerprint`, `sni`，并校验 `short-id` 为合法十六进制（非法节点直接跳过，避免 Clash 解析报错）
- **格式转换**: Python + PyYAML 生成 Clash YAML，QuantumultX 使用 Base64 URI 列表
- **容错机制**: HTTP 请求自动重试（含 403/429 退避），超时时间 60 秒；上游按 IP 段封锁时由 macOS 备份链路接管

## 📝 部署配置

在仓库 Settings → Secrets and variables → Actions 中配置：

- `GIST_TOKEN`: GitHub 个人访问令牌（需 gist 权限）
- `GIST_ID`: 目标公开 Gist 的 ID

## ⚠️ 注意事项

- 订阅链接固定不变，客户端刷新间隔建议小于脚本刷新间隔
- 节点信息由各 VPN 服务商提供，本项目仅做格式转换和托管
- GitHub Actions 运行日志可在 Actions 页面查看
- 如链式循环中断，cron 备用触发器会自动恢复
