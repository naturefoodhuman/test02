<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
-->

# Pattern：data-acquisition（工厂通用取数层 · FB-6 L1）

> 工厂级通用能力：从**官方公开渠道**合规取数。
> **核心理念：不暴力爬、不封号、不替你登录第三方账号。** 满足老板"落地成功率优先 + 账号安全"。

## 为什么不是"全自动爬虫"
调研事实（见 docs/research/data-acquisition-feasibility.md）：
- 中国执行信息公开网/裁判文书网/gsxt 等官方渠道**都有验证码或需登录**，暴力直抓会撞验证码 + 触发反爬 + 违反 ToS。
- 强风控平台（企查查/天眼查）账号自动抓**有真实封号风险**。

→ 所以本层做"**取数协调器**"而非爬虫：
1. 维护官方渠道的【查询方法 + 直达入口 + 风控等级】注册表；
2. 给定债务人，**自动生成"待查清单"**（去哪查、查什么、怎么查）；
3. 遇验证码/登录 → **停下来等你手动完成**（L2 人在环）；
4. 把查回的结果**结构化归档**，供策略报告引用。

## 三层取数模式
- **L1_public**：纯公开无验证码（如法律法规库）→ 可直接生成链接。
- **L2_human**：有验证码/登录（执行网/文书网/gsxt）→ 系统辅助打开，**验证码/登录你手动过**。
- **L3_account**：账号自动抓（**默认关闭**，需逐次授权，账号安全>数据）。本 Pattern 默认不启用。

## 用法
```bash
cd _factory/patterns/data-acquisition
python -m pytest -q                        # 8 passed（沙箱核心逻辑）

# 为债务人生成官方渠道待查清单
python -m acquisition.cli "张三" --type person --region 浙江杭州 -o ./out
python -m acquisition.cli "某某公司" --type company -o ./out
# 装好后命令：forge-acquire "张三" -o ./out
```

## 输出
- `待查清单_<名>.md`：人话待查清单（每个官方渠道怎么查、风险、验证码/登录提示）。
- `plan_<名>.json`：机器可读计划。
- 查完后用 `archive_results()` 把结果归档为 `results_<名>.json`（结构化证据）。

## 覆盖的官方数据源（讨债核心）
| 渠道 | 能查 | 模式 |
|---|---|---|
| 中国执行信息公开网 | 失信/限高/被执行人/财产处置 | L2(验证码) |
| 中国裁判文书网 | 涉诉历史/判决/财产线索 | L2(登录+验证码) |
| 国家企业信用信息公示系统 | 工商/股东/对外投资 | L2(滑块) |
| 国家法律法规数据库 | 法条核对(防幻觉) | L1(公开) |

## L2 浏览器辅助（人在环，已实现 FB-6 L2）
`browser_assist.py`：用 browser-use（接 GLM via LiteLLM 网关）半自动查询官方渠道。
**核心安全约束**：headless=False（显示窗口）、遇验证码/登录**暂停等人工**、不猜账号密码、不绕验证码。
```bash
# 真机启用 L2
pip install browser-use playwright && playwright install chromium
# 确保 LiteLLM 网关在跑（GLM 驱动）：bash _infra/start-litellm.sh
python -m acquisition.cli "张三" --type person --l2 -o ./out
# 浏览器会打开官方页自动填查询；遇验证码/登录时它会停下让你手动完成，再继续抓结果
```
沙箱无 browser-use 时 `--l2` 自动降级为安装指引，不报错。

## 最后验证
- 2026-06-11：沙箱 `pytest` 11 passed（含 L2 3 项）；CLI 生成清单 + `--l2` 降级实跑通过。
