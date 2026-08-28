/**
 * 红盾（Red Shield）自动注册 & 获取节点
 * 支持动态 SIGN + TIMESTAMP
 * 输出所有节点的 ss:// 链接
 * 作者频道 https://t.me/GieGie777
 * 兼容 Quantumult X / Surge / Loon / Node.js
 */

// -------- 常量与配置 --------
const SALT = "NjNXNzA4SXcyOXBsazRCQ0g1MW4=";
const HOST = "http://207.148.33.174";
const UA = "pt=IOS,version=1.0.3,verId=10,system=16.2,bundleId=com.red.shield,deviceId={{DEVICE}},lang=zh-Hans-US,brand=Apple,model=iPhone13-4,net=4G;";

// 设备 ID（留空则自动生成；若要固定账号，可手动赋值如 "37F0C325-4768-4D39-B487-7EC712E54998"）
let DEVICE = "";

// -------- 辅助函数 --------
function generateDeviceId() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16).toUpperCase();
    });
}

// MD5 纯 JS 实现
function md5(str) {
    function rl(n, c) { return (n << c) | (n >>> (32 - c)); }
    function cmn(q, a, b, x, s, t) { a = (((a + q) | 0) + ((x + t) | 0)) | 0; return (((rl(a, s)) + b) | 0); }
    function ff(a, b, c, d, x, s, t) { return cmn((b & c) | (~b & d), a, b, x, s, t); }
    function gg(a, b, c, d, x, s, t) { return cmn((b & d) | (c & ~d), a, b, x, s, t); }
    function hh(a, b, c, d, x, s, t) { return cmn(b ^ c ^ d, a, b, x, s, t); }
    function ii(a, b, c, d, x, s, t) { return cmn(c ^ (b | ~d), a, b, x, s, t); }
    function toBytes(s) {
        const utf8 = unescape(encodeURIComponent(s));
        const b = []; for (let i = 0; i < utf8.length; i++) b.push(utf8.charCodeAt(i) & 0xff);
        return b;
    }
    const bytes = toBytes(str);
    const n = bytes.length;
    const words = [];
    for (let i = 0; i < n; i++) words[i >> 2] |= bytes[i] << ((i % 4) * 8);
    words[n >> 2] |= 0x80 << ((n % 4) * 8);
    words[(((n + 8) >> 6) + 1) * 16 - 2] = n * 8;
    let a = 1732584193, b = -271733879, c = -1732584194, d = 271733878;
    for (let i = 0; i < words.length; i += 16) {
        const oa = a, ob = b, oc = c, od = d;
        const x = (j) => words[i + j] | 0;
        a = ff(a, b, c, d, x(0), 7, -680876936); d = ff(d, a, b, c, x(1), 12, -389564586);
        c = ff(c, d, a, b, x(2), 17, 606105819); b = ff(b, c, d, a, x(3), 22, -1044525330);
        a = ff(a, b, c, d, x(4), 7, -176418897); d = ff(d, a, b, c, x(5), 12, 1200080426);
        c = ff(c, d, a, b, x(6), 17, -1473231341); b = ff(b, c, d, a, x(7), 22, -45705983);
        a = ff(a, b, c, d, x(8), 7, 1770035416); d = ff(d, a, b, c, x(9), 12, -1958414417);
        c = ff(c, d, a, b, x(10), 17, -42063); b = ff(b, c, d, a, x(11), 22, -1990404162);
        a = ff(a, b, c, d, x(12), 7, 1804603682); d = ff(d, a, b, c, x(13), 12, -40341101);
        c = ff(c, d, a, b, x(14), 17, -1502002290); b = ff(b, c, d, a, x(15), 22, 1236535329);
        a = gg(a, b, c, d, x(1), 5, -165796510); d = gg(d, a, b, c, x(6), 9, -1069501632);
        c = gg(c, d, a, b, x(11), 14, 643717713); b = gg(b, c, d, a, x(0), 20, -373897302);
        a = gg(a, b, c, d, x(5), 5, -701558691); d = gg(d, a, b, c, x(10), 9, 38016083);
        c = gg(c, d, a, b, x(15), 14, -660478335); b = gg(b, c, d, a, x(4), 20, -405537848);
        a = gg(a, b, c, d, x(9), 5, 568446438); d = gg(d, a, b, c, x(14), 9, -1019803690);
        c = gg(c, d, a, b, x(3), 14, -187363961); b = gg(b, c, d, a, x(8), 20, 1163531501);
        a = gg(a, b, c, d, x(13), 5, -1444681467); d = gg(d, a, b, c, x(2), 9, -51403784);
        c = gg(c, d, a, b, x(7), 14, 1735328473); b = gg(b, c, d, a, x(12), 20, -1926607734);
        a = hh(a, b, c, d, x(5), 4, -378558); d = hh(d, a, b, c, x(8), 11, -2022574463);
        c = hh(c, d, a, b, x(11), 16, 1839030562); b = hh(b, c, d, a, x(14), 23, -35309556);
        a = hh(a, b, c, d, x(1), 4, -1530992060); d = hh(d, a, b, c, x(4), 11, 1272893353);
        c = hh(c, d, a, b, x(7), 16, -155497632); b = hh(b, c, d, a, x(10), 23, -1094730640);
        a = hh(a, b, c, d, x(13), 4, 681279174); d = hh(d, a, b, c, x(0), 11, -358537222);
        c = hh(c, d, a, b, x(3), 16, -722521979); b = hh(b, c, d, a, x(6), 23, 76029189);
        a = hh(a, b, c, d, x(9), 4, -640364487); d = hh(d, a, b, c, x(12), 11, -421815835);
        c = hh(c, d, a, b, x(15), 16, 530742520); b = hh(b, c, d, a, x(2), 23, -995338651);
        a = ii(a, b, c, d, x(0), 6, -198630844); d = ii(d, a, b, c, x(7), 10, 1126891415);
        c = ii(c, d, a, b, x(14), 15, -1416354905); b = ii(b, c, d, a, x(5), 21, -57434055);
        a = ii(a, b, c, d, x(12), 6, 1700485571); d = ii(d, a, b, c, x(3), 10, -1894986606);
        c = ii(c, d, a, b, x(10), 15, -1051523); b = ii(b, c, d, a, x(1), 21, -2054922799);
        a = ii(a, b, c, d, x(8), 6, 1873313359); d = ii(d, a, b, c, x(15), 10, -30611744);
        c = ii(c, d, a, b, x(6), 15, -1560198380); b = ii(b, c, d, a, x(13), 21, 1309151649);
        a = ii(a, b, c, d, x(4), 6, -145523070); d = ii(d, a, b, c, x(11), 10, -1120210379);
        c = ii(c, d, a, b, x(2), 15, 718787259); b = ii(b, c, d, a, x(9), 21, -343485551);
        a = (a + oa) | 0; b = (b + ob) | 0; c = (c + oc) | 0; d = (d + od) | 0;
    }
    const hex = (num) => { let s = ""; for (let i = 0; i < 4; i++) s += ("0" + ((num >> (i * 8)) & 0xff).toString(16)).slice(-2); return s; };
    return hex(a) + hex(b) + hex(c) + hex(d);
}

// 签名函数（修复：强制转换参数值为字符串）
function sign(params, ts) {
    let s = "";
    const keys = Object.keys(params).sort();
    for (const k of keys) {
        const val = String(params[k]);   // 关键：确保数字型 uid 也能被拼接
        s += `{${k}}{${val}}`;
    }
    s += SALT + ts;
    return md5(s);
}

// 构建请求（自动添加 SIGN 和 TIMESTAMP）
function buildRequest(path, params, token, uid) {
    const ts = String(Math.floor(Date.now() / 1000));
    const allParams = Object.assign({}, params);
    if (token) allParams.token = token;
    if (uid) allParams.uid = uid;
    const signVal = sign(allParams, ts);

    const headers = {
        "Accept-Encoding": "gzip, deflate",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "207.148.33.174",
        "User-Agent": UA.replace("{{DEVICE}}", DEVICE),
        "Accept-Language": "zh-Hans-US;q=1, en-GB;q=0.9, en-US;q=0.8, zh-Hant-US;q=0.7",
        "SIGN": signVal,
        "TIMESTAMP": ts
    };

    const bodyParts = [];
    for (const [k, v] of Object.entries(allParams)) {
        if (v !== undefined && v !== null) {
            bodyParts.push(`${k}=${encodeURIComponent(String(v))}`);
        }
    }
    const body = bodyParts.join("&");

    return {
        url: HOST + path,
        method: "POST",
        headers: headers,
        body: body
    };
}

// -------- btoa polyfill（Base64 编码）--------
function btoaPolyfill(str) {
    // 若环境自带 btoa 则直接使用
    if (typeof btoa === "function") return btoa(str);
    // 纯 JS 实现（仅支持 ASCII）
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let output = "";
    let i = 0;
    while (i < str.length) {
        const a = str.charCodeAt(i++);
        const b = i < str.length ? str.charCodeAt(i++) : 0;
        const c = i < str.length ? str.charCodeAt(i++) : 0;
        const triplet = (a << 16) | (b << 8) | c;
        output += chars.charAt((triplet >> 18) & 63);
        output += chars.charAt((triplet >> 12) & 63);
        output += chars.charAt((triplet >> 6) & 63);
        output += chars.charAt(triplet & 63);
    }
    // 补 =
    const len = str.length % 3;
    if (len === 1) output = output.slice(0, -2) + "==";
    else if (len === 2) output = output.slice(0, -1) + "=";
    return output;
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
const $ = new Env("红盾节点获取");

!(async () => {
    try {
        // 若未指定设备 ID，则随机生成
        if (!DEVICE) {
            DEVICE = generateDeviceId();
            $.log(`自动生成设备 ID: ${DEVICE}`);
        }

        // 基础参数（所有接口公用）
        const baseParams = {
            bundleId: "com.red.shield",
            channel: "10000",
            deviceId: DEVICE,
            lang: "zh-CN",
            platform: "2",
            ver: "3"
        };

        // 1. 登录（注册）-> 获取 token 和 uid
        const loginReq = buildRequest("/api/user.loginByDeviceId", baseParams);
        $.log(`① 登录请求: ${loginReq.url}`);
        const loginResp = await $.http(loginReq);
        if (loginResp.response_status?.code !== 0) {
            throw new Error(`登录失败: ${JSON.stringify(loginResp)}`);
        }
        const token = loginResp.response_data?.token;
        const uid = loginResp.response_data?.userinfo?.uid;
        if (!token || !uid) {
            throw new Error(`未获取到 token 或 uid: ${JSON.stringify(loginResp)}`);
        }
        $.log(`✅ 登录成功: uid=${uid}, token=${token}`);

        // 2. 获取节点列表（需要 token 和 uid）
        const nodeReq = buildRequest("/api/node.getNodeList", baseParams, token, uid);
        $.log(`② 获取节点列表请求: ${nodeReq.url}`);
        const nodeResp = await $.http(nodeReq);
        if (nodeResp.response_status?.code !== 0) {
            throw new Error(`获取节点列表失败: ${JSON.stringify(nodeResp)}`);
        }
        const nodes = nodeResp.response_data;
        if (!Array.isArray(nodes) || nodes.length === 0) {
            throw new Error("节点列表为空或格式错误");
        }
        $.log(`✅ 获取到 ${nodes.length} 个节点`);

        // 3. 将节点转换为 ss:// 链接
        const ssLinks = nodes.map(node => {
            const name = node.name || `${node.country}-${node.city}`;
            const method = node.method || "aes-256-cfb";
            const pwd = node.password;
            const ip = node.ip;
            const port = node.port;
            // 构建 userinfo: method:password
            const userinfo = `${method}:${pwd}`;
            const base64Userinfo = btoaPolyfill(userinfo);
            return `ss://${base64Userinfo}@${ip}:${port}#${encodeURIComponent(name)}`;
        });

        // 拼接成多行字符串（方便复制）
        const allLinks = ssLinks.join("\n");
        $.log(`③ 共生成 ${ssLinks.length} 条 ss:// 链接`);
        // 日志中输出纯链接列表（无序号）
        $.log(`所有节点链接（共${ssLinks.length}条）：\n${allLinks}`);

        // 通知展示（如果内容太长可能被截断，可在日志中查看完整）
        $.msg("红盾节点", `共 ${ssLinks.length} 个节点`, allLinks.substring(0, 500) + (allLinks.length > 500 ? "\n…（详见日志）" : ""));

    } catch (e) {
        $.log(`❌ 错误: ${e.message}`);
        $.msg("红盾脚本", "失败", e.message);
    } finally {
        $.done();
    }
})();
