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

## ⚙️ 架构与工作原理

本项目采用 **云端 Actions + 常驻轻量服务器** 双轨协同架构，彻底解决上游 IP 拦截问题，达成真·24小时无感永续：

1. **快猫 VPN（常驻服务器专线 + Jitter 防封）**：
   - 因快猫上游对 GitHub Actions 云端 IP 段严密拦截（HTTP 403），现部署于 24 小时常驻 Linux 服务器（如 `129.146.252.112`）。
   - 每 13 分钟由 Crontab 调度，内置 **5~45 秒随机 Jitter 扰动机制** 打散请求时间戳，模拟真实设备请求，彻底规避上游频率限制与 IP 封锁。
   - 采用标准 UUID4 动态注册，彻底杜绝历史碰撞（`邮箱已在系统中存在`），并在本地将 Reality 参数安全清洗后直更 Gist。
2. **Anyun & 红盾 VPN（GitHub Actions 自动化流水线）**：
   - 通过 `renew_anyun_hongdun.yml` 15 分钟链式自触发循环运行。
   - 配备 `trigger_anyun_hongdun.yml` 定时冷启动兜底，保证循环不中断。
3. **统一聚合中心（GitHub Gist）**：
   - 三平台所有节点数据实时汇总更新至公开 Gist，客户端订阅地址永久固定不变，随用随刷。

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
