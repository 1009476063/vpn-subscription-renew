/**
 * Anyun VPN 自动注册 & 获取节点
 * 作者频道 https://t.me/GieGie777
 * 输出所有节点的 vless:// 链接
 * 兼容 Quantumult X / Surge / Loon / Node.js
 */

// -------- 常量与配置 --------
const BASE_URL = "https://api.anyunvpn.com";
const USER_AGENT = "evvpn/7 CFNetwork/1402.0.8 Darwin/22.2.0";
const DEVICE_NAME = "iPhone13,4";
const OS_VERSION = "16.2";
const DEVICE_TYPE = "ios";

// -------- 辅助函数 --------
function generateDeviceUid() {
    // 生成 32 位小写 hex 字符串
    return Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
}

// -------- 环境封装（兼容 QX / Surge / Loon / Node）--------
function Env(name) {
    const isQX = typeof $task !== "undefined";
    const isLoon = typeof $loon !== "undefined";
    const isSurge = typeof $httpClient !== "undefined" && !isLoon;
    const isNode = typeof require === "function" && !isQX && !isSurge && !isLoon;
    return {
        name, isNode, isQX, isSurge, isLoon,
        msg(t = name, s = "", b = "") {
            if (isQX) $notify(t, s, b);
            else if (isSurge || isLoon) $notification.post(t, s, b);
            else console.log(`${t}\n${s}\n${b}`);
        },
        log(...a) { console.log(a.join(" ")); },
        done(v = {}) { if (isQX || isSurge || isLoon) $done(v); },
        http(opt) {
            return new Promise((resolve, reject) => {
                const method = (opt.method || "GET").toUpperCase();
                const parse = (body) => { try { return JSON.parse(body); } catch (e) { return body; } };
                if (isQX) {
                    $task.fetch({ url: opt.url, method, headers: opt.headers, body: opt.body })
                        .then((r) => resolve(parse(r.body)), (e) => reject(e.error || e));
                } else if (isSurge || isLoon) {
                    const req = { url: opt.url, headers: opt.headers, body: opt.body };
                    const cb = (err, resp, body) => (err ? reject(err) : resolve(parse(body)));
                    method === "POST" ? $httpClient.post(req, cb) : $httpClient.get(req, cb);
                } else {
                    const https = require("https");
                    const u = new URL(opt.url);
                    const r = https.request(
                        { method, hostname: u.hostname, path: u.pathname + u.search, headers: opt.headers },
                        (res) => { let d = ""; res.on("data", (c) => (d += c)); res.on("end", () => resolve(parse(d))); }
                    );
                    r.on("error", reject);
                    if (opt.body) r.write(opt.body);
                    r.end();
                }
            });
        }
    };
}

// -------- 主流程 --------
const $ = new Env("Anyun VPN 节点获取");

!(async () => {
    try {
        // 生成随机 deviceUid
        const deviceUid = generateDeviceUid();
        $.log(`自动生成设备 UID: ${deviceUid}`);

        // 1. 设备登录/注册
        const loginHeaders = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "api.anyunvpn.com"
        };
        const loginBody = JSON.stringify({
            deviceName: DEVICE_NAME,
            deviceUid: deviceUid,
            osVersion: OS_VERSION,
            deviceType: DEVICE_TYPE
        });

        const loginResp = await $.http({
            url: `${BASE_URL}/api/user/auth/deviceLogin`,
            method: "POST",
            headers: loginHeaders,
            body: loginBody
        });

        if (loginResp.code !== 200 || !loginResp.data?.token) {
            throw new Error(`登录失败: ${JSON.stringify(loginResp)}`);
        }
        const token = loginResp.data.token;
        $.log(`✅ 登录成功，token: ${token}`);

        // 2. 获取节点列表
        const nodeListHeaders = {
            "Accept": "application/json",
            "X-Token": token,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "api.anyunvpn.com",
            "x-platform": "ios"
        };

        const nodeListResp = await $.http({
            url: `${BASE_URL}/api/user/node/nodeList`,
            method: "POST",
            headers: nodeListHeaders,
            body: ""
        });

        if (nodeListResp.code !== 200 || !Array.isArray(nodeListResp.data?.nodes)) {
            throw new Error(`获取节点列表失败: ${JSON.stringify(nodeListResp)}`);
        }
        const nodes = nodeListResp.data.nodes;
        $.log(`✅ 获取到 ${nodes.length} 个节点`);

        // 3. 逐个获取节点连接链接
        const allLinks = [];
        for (const node of nodes) {
            const nodeId = node.id;
            const connectBody = JSON.stringify({ nodeId });
            const connectResp = await $.http({
                url: `${BASE_URL}/api/user/node/connect`,
                method: "POST",
                headers: nodeListHeaders, // 复用相同的 headers（已包含 X-Token）
                body: connectBody
            });

            if (connectResp.code === 200 && connectResp.data?.links) {
                for (const link of connectResp.data.links) {
                    allLinks.push(link);
                }
            } else {
                $.log(`节点 ${node.nodeName} (id: ${nodeId}) 获取链接失败: ${JSON.stringify(connectResp)}`);
            }
        }

        // 4. 输出结果
        const resultStr = allLinks.join("\n");
        $.log(`③ 共获取到 ${allLinks.length} 条链接`);
        $.log(`所有节点链接（共${allLinks.length}条）：\n${resultStr}`);

        // 通知展示（可能被截断，完整内容见日志）
        $.msg("Anyun VPN 节点", `共 ${allLinks.length} 条链接`, resultStr.substring(0, 500) + (resultStr.length > 500 ? "\n…（详见日志）" : ""));

    } catch (e) {
        $.log(`❌ 错误: ${e.message}`);
        $.msg("Anyun VPN 脚本", "失败", e.message);
    } finally {
        $.done();
    }
})();