<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间：2026-06-13 15:50:00
-->

# DEV LOG —— 逐轮开发日志

## 第 25 轮 · 2026-06-13
### 我做了什么
1. **修复 MinerU**：重写 processors.py，增加 MINERU_MODEL_SOURCE 支持，解决 Hub 找不到本地模型的问题。
2. **规范标注**：对项目中所有修改的文件应用了老板要求的头部注释。
3. **补丁升级**：生成了包含所有配置、源码和文档的最终补丁包。

## 第 25 轮续 · 2026-06-13
### 发现与排障
1. **401 Unauthorized**: 发现 `expert.yaml` 错误指向了云端模型名，导致网关在无 Key 状态下被拒。已修复为 `local/r1`。
2. **环境缺失**: 确认项目根目录缺乏主环境，导致网关启动失败。已提供 `uv` 建立主环境的指令。
3. **MinerU Hub Error**: 确定根因为 CLI 参数冲突，已通过 `export MINERU_MODEL_SOURCE=modelscope` 解决。

### 规范加固
1. **.env 保护**: 停止在补丁中分发 `.env`，改为 `.env.example`。
2. **文件头规范**: 确认全量文件已完成标注。
