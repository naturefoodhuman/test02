<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

---
skill_id: security-review
name: 安全审查
phase: [HARDEN]
load_when: "HARDEN 阶段，对生成代码做安全/性能/依赖审查时"
last_verified: 2026-06-10
version: 0.1
---

# 技能：安全审查（HARDEN 阶段）

## 何时用
- HARDEN 阶段（FR-001-14, AC-005）。首选 cloud/glm，GLM 挂则 local/primary 并标注"待人工复核"。

## 核心步骤
1. **分批审查**（风险#7）：按模块分批喂代码，避免上下文超限，结果汇总到 SECURITY_REVIEW.md。
2. **威胁建模**：输入验证、认证授权、注入、密钥泄露、依赖漏洞、SSRF/路径穿越。
3. **依赖审计**：`uv pip list` + 已知 CVE 检查 → DEPENDENCY_AUDIT.md。
4. **性能分析**：明显的 N+1、阻塞 IO、内存热点 → PERFORMANCE_ANALYSIS.md。
5. **重大决策**：可触发 Manual Gate（境外模型二次评审，结果写 external-review/）。

## 检查清单
- [ ] 无已知高危漏洞（AC-005）
- [ ] 密钥不硬编码（在 .env / config）
- [ ] 输入有校验
- [ ] 依赖无已知高危 CVE
- [ ] 若用本地模型降级审查，已标注"待人工复核"

## 反模式
- 一次性把整个代码库塞进上下文（超限/质量下降）。
- 把"LLM 说没问题"当成通过。

## 输出物
- `docs/harden/SECURITY_REVIEW.md`、`PERFORMANCE_ANALYSIS.md`、`DEPENDENCY_AUDIT.md`
