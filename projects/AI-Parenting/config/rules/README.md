# config/rules —— 规则包目录（APC-T018）

> 规则引擎的规则定义以 YAML 规则包形式存放于此，按域分目录。
> 架构依据：`docs/ARCHITECTURE_FINAL.md` §10.2、§18；`docs/ENGINEERING_DESIGN.md` §13.2。

---

## 目录约定

```
config/rules/
├── README.md                 # 本文件
├── triage/                   # 分诊/阈值规则域
│   └── base-1.yaml           # <pack>-<version>.yaml
├── medication/               # 用药规则域（APC-T020）
├── vaccine/                  # 疫苗规则域（APC-T022）
└── growth/                   # 生长规则域（APC-T023）
```

每个域一个子目录，规则包文件名 `<pack>-<version>.yaml`。

---

## YAML Schema

```yaml
policy_type: triage           # 策略类型（与 evidence_policy.policy_type 对齐）
region: CN                    # 区域（影响规则版本，默认 CN）
version: 1                    # 版本号（强制递增，架构 §18）
effective_from: 2026-08-16T00:00:00+08:00  # 生效时间（ISO8601，timezone-aware）
source: "国家免疫规划/WHO 0-5岁生长标准"    # 来源
rule_text: |                  # 规则文本（EvidencePolicy.rule_text，审计追溯）
  3 月龄以下直肠温 ≥38°C 为强红线。
display_text: |               # 展示文本（EvidencePolicy.display_text，UI 展示）
  3 个月以下宝宝体温达到 38°C 需立即就医。
rules:                        # 规则列表（顺序求值，首个匹配产出）
  - rule_id: fever_under_3mo_red   # 规则包内唯一 id
    conditions:               # 全部满足则匹配（AND）
      - op: lt                # 算子：eq/ne/lt/lte/gt/gte/in/not_in/range
        field: baby_age_days  # 字段路径（顶层或 variables.xxx 嵌套）
        value: 90              # 3 月龄 ≈ 90 天
      - op: gte
        field: variables.temperature_c
        value: 38.0
    action:                   # 匹配时产出
      verdict: block          # allow/block/warn/info
      outputs:                # dose/threshold 等（只有 RuleModule 可产出）
        alert_level: red
      reason_code: fever_under_3mo_red   # 机读原因码
      evidence_text: "3 月龄以下 ≥38°C 强红线（PRD §11.9）"
# hash: <sha256>              # 可选：loader 计算并自校验；声明则比对，不一致报错
```

---

## 算子（kernel.py）

| op | 语义 | value |
|---|---|---|
| `eq` / `ne` | 等于 / 不等于 | 标量 |
| `lt` / `lte` / `gt` / `gte` | 小于 / ≤ / 大于 / ≥ | 数值（actual/expected 为 None 时保守返回 False） |
| `in` / `not_in` | 属于 / 不属于 | 列表 |
| `range` | 闭区间 [lo, hi] | `[lo, hi]` |

字段路径：顶层字段（`baby_age_days` / `weight_kg`）或 `variables.xxx` 嵌套（如 `variables.temperature_c`）。

---

## 新增规则包流程（ENGINEERING_DESIGN §13.2）

1. 在 `config/rules/<domain>/` 新建 `<pack>-<version>.yaml`（version 严格递增）。
2. 需新算子则扩展 `server/app/rule_engine/kernel.py`（否则不改内核）。
3. 在 `server/tests/golden/rules/` 补黄金用例（固定输入断言 RuleResult）。
4. `make rules-validate`（Pydantic + hash 校验）。
5. Admin API `POST /api/v1/rules/policies/activate` 激活（旧版本自动 `effective_to`，APC-T019）。
6. 审计自动记录变更人/版本。

---

## 校验

```bash
make rules-validate    # python -m server.app.rule_engine.loader --validate config/rules
```

校验内容：YAML → Pydantic `RulePack` schema + 内容 hash 自校验（声明 `hash` 则比对）。
