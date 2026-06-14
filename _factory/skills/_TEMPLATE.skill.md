# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-13 18:45:00 CST

# SKILL.md 技能模板

> 用途：定义一个可复用的专家技能，任何评审专家在需要时可加载。
> 设计：纯 Markdown 文件，drop 到 `_factory/skills/` 目录即可被专家发现。

---

## meta
- **id**: skill-id（唯一标识）
- **name**: 技能名称
- **version**: 0.1.0
- **category**: 分类（risk/compliance/execution/legal/acquisition/...）
- **author**: 创建者
- **created**: 2026-06-13

## description
简短描述该技能的用途和适用场景（1-2 句话）。

## triggers
触发条件（当案件出现以下特征时，专家应自动加载此技能）：
- 触发词 1
- 触发词 2
- 触发词 3

## knowledge
技能的核心知识/规则/模板：

### 规则 1
描述...

### 规则 2
描述...

## output_format
该技能输出的结构化格式：

```json
{
  "skill_id": "",
  "result": "",
  "confidence": 0.0,
  "notes": []
}
```

## references
- 相关法律法规
- 判例引用
- 实务指南
