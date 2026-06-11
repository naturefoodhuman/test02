<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-11 23:10:00 CST
-->

---
skill_id: data-acquisition
name: 合规取数（官方公开渠道）
phase: [DISCOVERY, SPEC, BUILD]
load_when: "项目需要从外部官方渠道取数（如查执行/工商/裁判文书）时"
last_verified: 2026-06-11
version: 0.1
---

# 技能：合规取数（工厂通用能力 FB-6）

> 老板硬约束：账号安全 > 数据；落地成功率优先；不赌账号、不违 ToS。

## 三层取数原则（务必遵守）
- **L1 公开渠道（默认首选）**：官方公开数据，生成直达查询入口。
- **L2 人在环（有验证码/登录时）**：系统辅助，**验证码/登录由人手动完成**，不暴力绕过。
- **L3 账号自动抓（默认关闭）**：仅 L1/L2 不足、且老板逐次显式授权时；限频/拟人化/失败即停/账号安全优先。

## 核心步骤
1. 用 `_factory/patterns/data-acquisition`：`python -m acquisition.cli "<名>" --type person -o out`。
2. 得到"待查清单"→ 按清单去官方渠道查（遇验证码/登录人工过）。
3. （可选 L2）`--l2` 启用浏览器辅助：browser-use 接 GLM 半自动打开页面，遇验证码/登录**停下等人工**。
   真机需 `pip install browser-use playwright` + LiteLLM 网关在跑。
4. 查回结果用 `archive_results()` 结构化归档。
5. 归档结果 + sources.yaml 可信度 → 喂给策略报告/RAG。

## 检查清单
- [ ] 优先 L1/L2，未经授权不启用 L3 账号抓取
- [ ] 强风控平台(企查查/天眼查)走官方API，不用账号爬
- [ ] 敏感信息(身份证号)本地处理、脱敏存储
- [ ] 每条结果留原文摘录作证据

## 反模式
- 暴力全自动爬官方渠道（撞验证码+反爬+违 ToS）。
- 用老板账号自动登录抓强风控平台（封号风险）。

## 输出物
- 待查清单(md) + 取数计划(json) + 结构化结果归档(json)。
