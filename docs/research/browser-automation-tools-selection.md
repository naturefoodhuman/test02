<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 01:30:00 CST
-->

# 工厂能力调研：浏览器自动化 / 取数工具选型（FB-6 增强）

> 来源：老板给的 30 款横评(微信公号) + browser-act SKILL.md + 多篇实测对比 + 老板补充"社交平台情报也重要"。
> 遵守规则 R2：调研最新主流方案后给结论。

## 一、5 大派系全景（30 款横评）
1. **Agent 浏览器框架**：browser-use(96.6k,主力)、agent-browser(Rust)、stagehand(TS)、nanobrowser(扩展)
2. **中文平台爬虫**：MediaCrawler(50.6k,小红书/抖音/快手/B站/微博/贴吧/知乎)、Agent-Reach、AutoCLI
3. **自适应爬虫**：Scrapling(58k,自动适应网页改版)
4. **MCP 浏览器服务器**：playwright-mcp(评分最高60,微软)、mcp-chrome、browser-use-mcp-server
5. **网站转 CLI**：OpenCLI(复用 Chrome 登录态)

## 二、针对【我们场景】的适配分析
我们的硬约束：①目标多为政务/官方网站(有验证码+登录) ②本机 M1 + 走 LiteLLM 网关(GLM/qwen) ③Token 成本 ④账号安全/合规 ⑤社交平台情报。

| 工具 | 适配 | 用途定位 |
|---|---|---|
| **browser-use**(已用) | ✅ 接 GLM/本地、headed 人在环、Python 同栈 | L2 程序化取数(官方渠道) |
| **browser-act** | ⭐ 内置验证码人工协助 + Confirmation Gate(敏感操作需确认) + 数据本地 | 交互式查询首选(Claude Code 内) |
| **MediaCrawler** | ✅ 七大社交平台 | 社交平台情报采集(博主实操经验) |
| playwright-mcp / Playwright CLI | 🟡 工业稳/CLI 省 Token | 备选底层 |
| stagehand | 🟡 TS 非主栈 | 不选 |
| Scrapling | 🟡 大规模自适应爬取 | 暂不需要 |

## 三、最终选型结论（老板第17轮拍板：三条腿）
1. **browser-use（接 GLM via LiteLLM）= L2 程序化取数**（官方渠道，已建于 data-acquisition）。
2. **browser-act = 交互式查询首选**（在 Claude Code 里直接查时用，验证码协助 + 安全确认更顺手）。
   - ⚠️ 权衡：第三方 CLI(browseract.com)；验证码协助会把**验证码图片**发其云端 API（官方声明不传 cookie/页面内容，数据其余全本地）。
   - 安装：`uv tool install browser-act-cli --python 3.12`。
3. **MediaCrawler = 社交平台情报源**（抖音/小红书/知乎/B站等博主的实时实操经验）。
   - ⚠️ 合规/风险：a) MediaCrawler 未标 License，**商用有风险**，**个人自用研究**相对安全；
     b) 抓取需登录态/有封号风险 → **沿用三层原则：优先看公开内容、必要时人在环、账号安全>数据**；
     c) 社交内容**质量参差** → **必须经 sources.yaml 可信度分级 + 多源交叉验证 + 去软文**(FB-5)，
        博主信息标 `self_media`(默认权重 0.3)，验证可靠再升级；遇"卖课/引流/夸大"打入 blacklist。

## 四、对工厂取数层的架构影响（FB-6 升级为 FB-6+）
```
取数层(data-acquisition)
├── L1 公开清单(官方渠道)            ← 已建
├── L2 browser-use(接 GLM,人在环)    ← 已建
├── L2' browser-act(交互式,验证码协助) ← 新增接入点(交互场景)
└── L3 社交情报(MediaCrawler)        ← 新增；产出经 FB-5 数据质量过滤后入情报库(intel)
```
- 社交情报采集结果 → 经数据质量分级 → 写入 debt-collection 的 **情报库(intel)** → 触发策略动态重算(ADR-006)。
- 这把"工具选型"和已建的 intel/data-quality 打通了。

## 五、给老板的诚实提示
- 社交平台抓取是这批工具里**法律灰度最高**的一环。个人自用研究风险低，但：不要商用、不要二次散布他人隐私、对"卖课/夸大成功率"内容保持警惕（已在 sources.yaml 给了拉黑标准）。
- 真正高价值且低风险的，仍是**官方渠道(L1)**；社交情报是**补充线索**，需交叉验证，不可当唯一依据。

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-12 01:30:00 | 初版：30款横评分析 + 三条腿选型(browser-use/browser-act/MediaCrawler) + 合规与数据质量联动 | Claude Sonnet 4.5 |
