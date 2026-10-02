# VPN 多源订阅聚合与无感永续服务

## 📋 项目简介

本项目实现多源 VPN 订阅的**高可用自动续订与分发**。采用 **macOS 本地主力通道 + 7x24h Linux 常驻服务器智能守护 + GitHub Actions 自动化流水线** 的多轨协同架构，彻底突破上游防火墙对机房云 IP 的拦截，实现节点在过期前自动刷新并替换至固定 Gist 地址，为 Clash 与 QuantumultX 客户端提供 7x24 小时无感永续订阅。

---

## 🔗 订阅链接

### 1. 快猫 VPN（约 10 分钟自动刷新，节点寿命 30 分钟）

| 客户端 | 订阅地址 (永久固定) |
|--------|-------------------|
| **Clash** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/vpn_subs_clash.txt` |
| **QuantumultX** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/vpn_subs_qx.txt?opt-parser=true&resource_parser=url` |

### 2. Anyun VPN（约 15 分钟自动刷新）

| 客户端 | 订阅地址 (永久固定) |
|--------|-------------------|
| **Clash** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/anyun_clash.txt` |
| **QuantumultX** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/anyun_qx.txt?opt-parser=true&resource_parser=url` |

### 3. 红盾 VPN（约 15 分钟自动刷新）

| 客户端 | 订阅地址 (永久固定) |
|--------|-------------------|
| **Clash** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/hongdun_clash.txt` |
| **QuantumultX** | `https://gist.githubusercontent.com/1009476063/98ee639023acbec7a4b086cc87cd2de7/raw/hongdun_qx.txt?opt-parser=true&resource_parser=url` |

> **QuantumultX 提示**：请在订阅链接后附带资源解析器参数（如 `?opt-parser=true&resource_parser=url`），配合 KOP-XIAO 等标准解析器即可完美自动识别解析。

---

## ⚙️ 架构与双机协同永续原理

由于快猫上游 API（`api.kuaimiaov4.com`）部署了 GSL 高防与严格的机房 IP 拦截策略（对 GitHub Actions 云端 Runner 与部分数据中心直接丢弃握手），单一依赖云端 Actions 无法达成 100% 可用率。因此系统升级为 **“主客协同 + 智能巡检 + 探针联动”** 完整闭环：

```mermaid
graph TD
    subgraph 主通道 - macOS 本地 (家宽环境)
        M[Mac 本地 launchd 定时器\n每 10 分钟运行] -->|家宽直连 API 取新订阅| A[快猫官方 API]
        M -->|更新节点池| G[GitHub Gist\n98ee639023acbec7a4b086cc87cd2de7]
        M -->|上报 status=up msg=Mac_synced_OK| K[Uptime Kuma\n心跳监控探针]
    end

    subgraph 守护通道 - 7x24h Linux 常驻服务器
        V[VPS Crontab 定时器\n每 10 分钟运行] -->|1. 检查 Gist 新鲜度| G
        V -->|新鲜度 < 20min| H[跳过重复请求\n上报 status=up msg=Gist_fresh_active] --> K
        V -->|失联兜底: 新鲜度 >= 20min| W[激活本地 WARP SOCKS5 隧道]
        W -->|代理穿透拉取新订阅| A
        W -->|应急补推| G
        W -->|上报 status=up msg=VPS_fallback_OK| K
    end

    subgraph 自动化流水线 - GitHub Actions
        GH[Actions 15分钟链式自触发] -->|定时自动化轮转| AH[Anyun & 红盾 API]
        GH -->|聚合更新| G
    end

    G -->|统一固定 URL 订阅| C[Clash / QuantumultX 客户端]
```

### 1. 双机协同机制
- **正常开机时（Mac 主打）**：Mac 本地通过系统自带 `launchd` 服务，利用原生家宽出口每 10 分钟静默刷新快猫节点并写入 Gist，成功后向 Uptime Kuma 推送 `status=up` 心跳。
- **智能免冲突巡检（VPS 守护）**：常驻 Linux 服务器每 10 分钟巡检 Gist `updated_at` 时间戳。检测到订阅池刚被 Mac 刷新且剩余寿命充足（`<20 分钟`）时，**直接上报健康心跳并主动跳过上游请求**，既防止重复刷频被上游风控，又彻底消除虚假红条报警。
- **关机/离线应急接管（VPS 兜底）**：当 Mac 关机、休眠或断网超过 20 分钟时，VPS 自动判定主通道失联，无缝激活自身配置的用户态 Cloudflare WARP 隧道进行应急续订与推流，达成真·7x24 小时不断连。

### 2. 探针与健康监控联动
- **分发源监控（Monitor 315）**：关键词探测 Gist 原始响应，验证客户端拉取可用性。
- **管道心跳监控（Monitor 316 - Push 模式）**：由 Mac 主通道与 VPS 守护通道双向点亮，无论谁负责当期刷新，均能实时维持绿色正常状态。

---

## 📁 项目目录结构

```text
├── .github/workflows/
│   ├── renew.yml                 # 快猫云端备用工作流（已停用云端调度，防封防爆额度）
│   ├── trigger.yml               # 快猫云端备用触发器（已停用）
│   ├── renew_anyun_hongdun.yml   # Anyun/红盾主工作流：15分钟链式自触发
│   └── trigger_anyun_hongdun.yml # Anyun/红盾备用触发器：cron 调度保活
├── mac_deploy/                   # macOS 本机守护部署套件
│   ├── refresh.sh                # 本机刷新脚本（含 Uptime Kuma 心跳联动）
│   ├── start.sh                  # 一键加载 launchd 后台开机自启
│   ├── stop.sh                   # 一键卸载与停止任务
│   └── com.tx.sync-kuaimao.plist # launchd 服务配置文件
├── server_deploy/                # Linux 常驻服务器守护部署套件
│   ├── refresh.sh                # 智能巡检与 WARP 应急兜底脚本
│   ├── setup_cron.sh             # 一键安装 crontab 定时调度（每 10 分钟）
│   └── env.example               # 服务器环境变量配置模板 (.env)
├── vpn_refresher.py              # 快猫订阅核心处理脚本（UUID4 设备注册 + Reality 清洗）
├── anyun_refresher.py            # Anyun 订阅核心处理脚本
├── hongdun_refresher.py          # 红盾 订阅核心处理脚本
├── Anyun.js                      # Anyun 抓包参考
└── hongdun.js                    # 红盾 抓包参考
```

---

## 🚀 部署指南

### A. macOS 本机部署（主通道推荐）

只要 Mac 处于开机状态，即可作为最稳定纯净的家宽更新源：

```bash
# 1. 确保已登录 GitHub CLI
gh auth login

# 2. 安装 Python 依赖
pip3 install requests pyyaml

# 3. 运行一键配置脚本
cd mac_deploy
./start.sh
```

- 查看实时运行日志：`tail -f ~/sync-kuaimao/refresh.log`
- 如需临时停用：`./stop.sh`

### B. Linux 常驻服务器部署（7x24h 关机守护）

适合部署在 Oracle、搬瓦工、轻量云等 VPS 上，作为关机后的后备电源：

```bash
# 1. 进入服务器部署目录
cd server_deploy

# 2. 配置环境变量
cp env.example .env
nano .env   # 填入具备 Gist 读写权限的 GIST_TOKEN 与 GIST_ID

# 3. 确保服务器具备 Python3 环境与 requests、pyyaml 库
pip3 install requests pyyaml

# 4. 安装定时调度任务（每 10 分钟自动执行并随机 Jitter）
./setup_cron.sh
```

---

## 🔧 技术保障特性

1. **Anti-Collision 设备生成**：采用标准 `uuid.uuid4()` 生成设备唯一标识，杜绝短前缀冲突引发的 `邮箱已在系统中存在` 上游报错。
2. **Reality 参数深度校验**：
   - 提取 `public-key`, `short-id`, `client-fingerprint`, `sni`；
   - 严格遵循 Mihomo/Clash 规范，校验 `short-id` 必须为偶数位合法十六进制且 $\le 16$ 字节；自动清洗剔除畸变节点，防止客户端配置报错撤销。
3. **YAML 标量类型安全引用**：针对十六进制短 ID（如 `87991e38`）强制做双引号字符串转义，规避 YAML 1.2 自动推断为科学计数浮点数导致的内核解析崩溃。
4. **日志自动滚动防爆盘**：脚本内建行数监控，超过 5000 行自动截断保留最新 3000 行，长期运行零维护成本。

---

## ⚠️ 客户端配置建议

- **刷新周期建议**：客户端本地订阅的自动刷新间隔建议设置为 **10 分钟或更短**（因快猫官方 UUID 寿命为 30 分钟，保持 10 分钟刷新可确保持续无感漫游）。
- **Gist 权限**：若自行部署，请确保 GitHub 个人令牌（PAT）拥有 `gist` 作用域授权。
