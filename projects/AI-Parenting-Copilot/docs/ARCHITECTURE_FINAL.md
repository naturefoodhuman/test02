# ARCHITECTURE_FINAL.md

> 项目：AI Parenting Copilot（家庭私有化 AI 育儿副驾驶系统）
> 文档定位：本项目唯一正式架构基线（Architecture Baseline）
> 文档位置建议：`projects/AI-Parenting-Copilot/docs/ARCHITECTURE_FINAL.md`
> 本文档是后续 ENGINEERING_DESIGN、TASK_BACKLOG 及 AI Agent 持续开发的唯一技术依据。

---

## 0. 文档定位与边界

本文档依据 `PRD.md`（业务需求唯一来源）与 `PROJECT_DOSSIER_V5.md`（FORGE Factory 工厂能力来源）推导得出。

- 业务需求：只来自 PRD，本文档不新增、不修改、不删除业务需求。
- 工厂能力：默认复用 FORGE Factory 已有能力；仅在 PRD 需求无法由工厂能力满足时新增模块。
- 项目隔离：本项目为独立项目，位于 `projects/AI-Parenting-Copilot/`。根目录 `PROJECT_DOSSIER_V*.md` 仅作为工厂能力与治理规则参考，不作为本项目需求或任务状态来源。
- 工厂能力复用清单见 §29 需求追溯矩阵。

---

## 1. 架构目标与设计铁律

### 1.1 决策铁律（源自 PRD §1.3）

架构层面任何取舍冲突，按如下优先级裁决：

> 记录摩擦最低 > 提醒最准时 > 告警必送达 > 预警最保守 > 数据最私有 > 规则不交给 LLM > AI 最克制

功能实现优先级：

> 高频 > 刚需 > 安全 > 医疗 > 自动化 > 炫技

### 1.2 架构硬约束

1. 本地优先（Local-first）：主控与权威数据在家庭局域网内 Mac M1 Max。
2. 离线可用：安卓端离线可完整记录，网络恢复自动补传，禁止因同步失败丢记录。
3. 规则与 LLM 分离：所有医疗/剂量/阈值判定由 Rule Engine 产出，LLM 不得自由计算或输出剂量。
4. 隐私边界：视频/图片/音频/医疗记录默认不出家庭局域网；云端 LLM 仅接收经隐私网关脱敏后的文本。
5. 告警必达：红/橙告警必须多通道送达并具本地兜底，红色告警未送达目标为 0。
6. 可审计：所有记录、告警、规则变更、LLM 调用、剂量拦截均写入不可删除审计日志。
7. 保守优先：预警宁缺毋滥；高风险提醒依赖多信号融合，不依赖单帧或单一传感器。

---

## 2. 系统整体架构

### 2.1 顶层视图

```text
┌──────────────────────────── 家庭局域网 (Home LAN) ────────────────────────────┐
│                                                                              │
│  [父亲安卓App]  [母亲安卓App]      [卧室IR摄像头] [客厅IR摄像头]  [mmWave+ESP32C6]│
│      │  RN + SQLite + PowerSync         │ RTSP/ISAPI  │ RTSP/ISAPI  │ MQTT     │
│      │  FCM 接收 / 全屏Intent           │             │             │          │
│      └──────────────┬──────────────────┴─────────────┴─────────────┘          │
│                     │                                                          │
│         ┌───────────▼──────────────── Mac M1 Max 家庭服务端 ────────────────┐  │
│         │  API Gateway ── Auth/RBAC                                        │  │
│         │  PowerSync Service ── PostgreSQL(权威源) ── Local File Store       │  │
│         │  Normalization ── Baby State Engine ── Rule Engine               │  │
│         │  Agent Orchestrator(含 Dose Interceptor) ── Domain Copilots      │  │
│         │  Notification Orchestrator                                       │  │
│         │  Camera/NVR Service ── mmWave Adapter ── MQTT Broker(Mosquitto)   │  │
│         │  Model Gateway(Smart Proxy/LiteLLM) ── Local LLM/VLM             │  │
│         │  Privacy Gateway ── Local RAG ── Memory Store                    │  │
│         │  Observability(Log/Metric/Trace) ── Device Health ── Backup      │  │
│         └───────────────────────────┬─────────────────────────────────────┘  │
│                                      │ 仅脱敏文本（经 Privacy Gateway）          │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                        ▼
                                  云端 LLM API（fallback，仅脱敏文本）
```

### 2.2 分层架构（源自 PRD §6.1）

```text
L1 输入层        文本/语音文本/图片/视频帧/传感器/表单/设备状态
      ↓
L2 归一化层      语音转事件 / 图片分类 / OCR / 去重 / 时间戳标准化 / 置信度评分
      ↓
L3 状态引擎层    Baby State Engine（当前睡眠、距上次喂奶、24h奶量、尿布、体温线、待办）
      ↓
L4 规则证据层    Rule Engine（中国疫苗规则 / WHO生长 / 用药规则 / 红黄蓝阈值 / 解释模板 + EvidencePolicy 版本化）
      ↓
L5 编排智能层    Agent Orchestrator + Domain Copilots（含 Dose Interceptor）
      ↓
L6 通知编排层    Notification Orchestrator（FCM / 摄像头扬声器 / 全屏告警 / 升级策略 / 定时提醒）
      ↓
L7 长期记忆层    M1硬事实 / M2家庭偏好 / M3行为基线 / M4短期上下文 / M5纠错记忆
```

分层规则：上层可调用下层；L5 只能通过 L4 获取医疗/剂量结论；L6 只消费 L3/L4/L5 已裁决的结构化告警；跨层调用不得绕过 Rule Engine。

---

## 3. 模块划分与职责边界

### 3.1 Mac 服务端模块（源自 PRD §6.2）

| 模块 | 职责 | 边界 | 来源 |
|---|---|---|---|
| API Gateway | 统一入口、路由、鉴权前置、限流 | 不含业务逻辑 | PRD §6.2 |
| Auth / RBAC | 家庭账号、角色、令牌、权限判定 | 不做业务规则 | PRD §3, §15.2 |
| PowerSync Service | 双向同步、冲突合并、权威源维护 | 复用，不自研同步 | PRD §7 / Factory-first |
| PostgreSQL | 权威关系型存储 | 唯一权威源 | PRD §7, §8 |
| Local File Store | 媒体/片段/导出文件、加密、索引 | 不入库大文件 | PRD §8.8, §15 |
| Normalization Service | 多源输入归一为 ObservationEvent | 不做医疗判定 | PRD §6.1, §8.5 |
| Baby State Engine | 派生 DerivedBabyState | 只做派生，不告警 | PRD §6.1, §8.6 |
| Rule Engine | 疫苗/用药/生长/分诊/阈值规则计算 | 唯一剂量/阈值产出者 | PRD §10.3, §11.11, §12 |
| Agent Orchestrator | 意图路由、上下文注入、Copilot 调度、Dose Interceptor、输出拦截 | 不产出剂量 | PRD §10.2 |
| Domain Copilots | 领域解释与结构化，见 §11 | 不绕过 Rule Engine | PRD §10.4 |
| Notification Orchestrator | 告警分级、通道编排、升级、定时提醒 | 不产生告警等级 | PRD §12, §13 |
| Camera/NVR Service | RTSP 拉流、ISAPI 事件、抓帧、片段、ROI、VLM 推理调度 | 睡眠会话内分析 | PRD §5, §11.6, §11.7 |
| mmWave Device Adapter | MQTT 订阅、雷达帧解析、SensorEvent 生成 | 不单独触发红色告警 | PRD §5.5, §11.8 |
| Model Gateway | 本地/云模型路由 | 复用 Smart Proxy/LiteLLM | Factory-first |
| Local LLM/VLM | 本地推理后端 | 复用工厂运行链路 | Factory-first |
| Privacy Gateway | 云端调用前脱敏、出站数据管控 | 云端仅收脱敏文本 | PRD §15.1 / Factory-first |
| Local RAG | 家庭知识与规则检索 | 本地 | Factory-first |
| Memory Store | 五层长期记忆读写 | 硬事实不入向量 | PRD §9 / Factory-first |
| Observability | 日志/指标/追踪/审计 | 审计不可删除 | PRD §15.4, §22.3 |
| Device Health Monitor | 设备/服务健康与灰色告警 | 60s 内发现离线 | PRD §22.1, §22.2 |
| Backup Service | 备份到 NAS、恢复演练 | 定期 | PRD §22.4 |

### 3.2 安卓端模块（源自 PRD §6.3, §14）

| 模块 | 职责 | 来源 |
|---|---|---|
| Auth & Family | 登录、家庭账号、设备注册 | PRD §14.2 |
| Today 首页 | 当前状态、统计、待办、告警、设备/同步状态 | PRD §11.1 |
| Quick Record | 大按钮快捷记录、计时器、语音、轻确认 | PRD §11.2 |
| Sleep Session UI | 会话开始/暂停/结束、画面、ROI 状态、事件片段 | PRD §11.6, §14.2.3 |
| Timeline | 事件列表、记录人、来源、编辑、撤销、合并 | PRD §14.2.4 |
| Alert Center | 告警列表、依据、证据、确认、反馈 | PRD §14.2.5 |
| Local SQLite + PowerSync Client | 离线写入、pending_sync、自动补传 | PRD §7.4 |
| FCM Receiver | 接收触发信号（仅 alert_id/level/type） | PRD §13.1, §15.1 |
| High-Priority Notification | 高优先级通道、全屏 Intent、锁屏、持续震动响铃 | PRD §13.3, §14.3 |
| Local Alarm Fallback | 进程存活时本地告警兜底 | PRD §13.3 |
| Background Sync | 后台同步任务、电池/自启白名单引导 | PRD §13.3, §14.1 |
| Night/Sleep Mode | 暗色、低亮、单手、纯语音 | PRD §14.3 |

---

## 4. 数据流与控制流

### 4.1 记录数据流（低摩擦记录，最高优先级）

```text
安卓 Quick Record / 语音文本
  → Logger Copilot 解析（语音/自由文本→结构化候选）
  → 轻确认（1 次）
  → 写本地 SQLite（标记 pending_sync）
  → PowerSync 上行
  → PostgreSQL 权威合并
  → Normalization → ObservationEvent
  → Baby State Engine 重算 DerivedBabyState
  → PowerSync 下行至两端
```

离线时：写本地 SQLite 完成记录，UI 即时反馈，网络恢复自动补传（PRD §7.4）。

### 4.2 传感器/摄像头证据流（睡眠会话内）

```text
mmWave → ESP32C6 → MQTT(baby/radar/telemetry) → mmWave Adapter → SensorEvent
Camera → RTSP 子码流抓帧 → Camera/NVR VLM 推理 → 姿态/遮挡/离床/夜醒候选事件
  → 多信号融合（Rule Engine 状态机）
  → 命中阈值 → Alert（含 level/evidence）
  → Notification Orchestrator
```

多信号融合状态机（源自 PRD §5.5 场景）：雷达 apnea 信号不直接红警；先向 NVR 请求视觉状态，按“家长在床边/床内无人/俯卧候选”分叉裁决。

### 4.3 健康/分诊控制流（规则优先）

```text
用户症状输入 / 体温记录
  → Orchestrator 意图=求助
  → Memory Store 注入（日龄、当前体重、百分位、近72h记录、家庭规则、过敏史、规则版本）
  → Rule Engine（红线判定、危险信号、就医阈值）
  → Health Triage Copilot（仅解释规则与风险，生成分诊输出结构）
  → Dose Interceptor（拦截任何 mg/ml/滴 自由输出）
  → 可追溯分诊卡片 + 证据链
  → 高风险 → Alert
```

### 4.4 用药安全控制流（Rule Engine 为执行器，源自 PRD §11.11）

```text
选择药物 → 校验月龄 → 校验体重时效 → 确认浓度 → 检查禁忌
  → Rule Engine 计算 mg → 换算 ml → 检查给药间隔 → 检查 24h 总量
  → 展示计算链路 → 父母二次确认 → 写入 MedicationLog
```

硬性拦截（PRD §11.11.4）：未知体重不出剂量；未知浓度不出 ml；体重过旧要求更新；<6 月龄布洛芬默认锁定；3 月龄以下 ≥38°C 触发红色分诊不优先给药；接近 24h 上限阻止重复给药；LLM 剂量输出一律拦截。

### 4.5 告警送达控制流（源自 PRD §13）

```text
Rule Engine 裁决 Alert(level)
  → Notification Orchestrator
    ├─ 通道1 双亲 FCM 高优先级（仅 alert_id/level/type）
    ├─ 通道2 Mac 客厅扬声器语音
    └─ 通道3 App 全屏 Intent + 持续震动响铃
  → 升级：0s 双推 → 60s Mac 重复语音 → 90s 手机加大音量/强震
  → 任一确认 → 全部停止 → 记录确认人/时间/设备
```

手机离线或进程被杀：Mac 扬声器与摄像头扬声器为强制本地兜底通道。

---

## 5. 生命周期与状态管理

### 5.1 事件生命周期

```text
created(pending_sync) → synced → normalized → derived-applied
                         ↘ corrected(correction_of) ↘ soft-deleted(is_deleted)
```

所有删除为软删除，保留审计（PRD §7.5）。

### 5.2 睡眠会话状态机（源自 PRD §11.6.2）

```text
not_started → active → paused → active → ended
```

触发进入：摄像头+mmWave 联合判定或家长主动开启。仅 active 内执行摄像头行为分析；非会话仅定时抓拍（PRD §11.6.6）。

### 5.3 告警状态机（源自 PRD §8.7）

```text
active → acknowledged → resolved
       → dismissed
```

反馈枚举：useful / false_positive / too_sensitive / already_known / ignored → 写入 M5 纠错记忆用于自动调阈（PRD §12.3）。

### 5.4 补剂/疫苗/用药待办状态

- 补剂：pending / completed / missed / skipped
- 疫苗：planned / completed / delayed / skipped
- 用药：按时间线记录，间隔与 24h 上限由 Rule Engine 校验

---

## 6. 数据架构

### 6.1 实体关系（源自 PRD §8.1）

```text
family
 ├─ user
 ├─ baby
 │   ├─ feeding_log / diaper_log / sleep_log / temperature_log
 │   ├─ supplement_log / vaccine_record / growth_log / medication_log
 │   ├─ symptom_event / jaundice_photo / milestone_log / media_asset
 │   ├─ alert / derived_baby_state
 │   └─ solid_food_log (V3/V4 预留)
 ├─ family_knowledge
 ├─ evidence_policy
 ├─ mother_health (V2)
 └─ audit_log
```

### 6.2 统一事件模型

所有输入先归一化为 `ObservationEvent`（PRD §8.5）。字段：event_id, baby_id, family_id, user_id, device_id, event_type, start_time, end_time, client_created_at, server_received_at, raw_input, normalized_payload, confidence, source, attachments, correction_of, is_deleted, created_at, updated_at。

领域派生表（feeding_log/diaper_log 等）由 ObservationEvent 归一化生成，保持事件溯源。

### 6.3 同步记录契约（源自 PRD §7.3）

每条可同步记录必须包含：event_id, baby_id, family_id, user_id, device_id, event_type, client_created_at, server_received_at, payload, source(manual|voice_text|camera|sensor|ai|system), confidence, is_deleted, correction_of。

### 6.4 关键实体字段基线

- BabyProfile：含 gestational_age_weeks、is_preterm、birth_weight_g、current_weight_g、known_allergies、vaccine_region(默认 CN) 等（PRD §3.2, §8.4）；数据结构预留多 baby_id。
- DerivedBabyState：Baby State Engine 输出（PRD §8.6）。
- Alert：level(gray/blue/yellow/orange/red)、evidence、recommended_action、feedback（PRD §8.7）。
- MediaAsset：local_path、thumbnail_path、camera_id、encrypted、tags（PRD §8.8）。
- SupplementLog / VaccineRecord / MedicationLog：均含规则/版本相关字段（PRD §8.9–8.11）。
- FamilyKnowledge：结构化 key/value/version（PRD §8.12）。
- EvidencePolicy：规则版本化载体，policy_type/region/version/effective_from/effective_to/source/rule_text/display_text（PRD §8.13）。
- MotherHealth(V2)：PRD §8.14。

### 6.5 长期记忆五层（源自 PRD §9）

| 层 | 存储 | 用途 |
|---|---|---|
| M1 硬事实 | PostgreSQL 关系型 | 不允许 LLM 猜测 |
| M2 家庭偏好 | FamilyKnowledge 结构化 | 注入上下文 |
| M3 行为基线 | 结构化 + 派生 | 趋势与预警 |
| M4 短期上下文 | 派生状态（近72h） | 临时推理 |
| M5 纠错记忆 | 结构化 + 少量向量(Local RAG) | 自适应调阈 |

健康类回答前 Orchestrator 必须注入：日龄、当前体重、体重百分位、近期相关记录、家庭规则、过敏史、近 72h 症状/用药/接种、相关规则版本（PRD §9）。

---

## 7. 存储架构

| 存储 | 内容 | 位置 |
|---|---|---|
| PostgreSQL | 权威关系数据、事件、派生状态、告警、审计 | Mac 本地 |
| SQLite | 安卓端本地事件、离线队列 | 手机 |
| Local File Store | 媒体缩略图、事件片段、导出 PDF/MD | Mac 本地文件系统 |
| 摄像头 microSD | 原始视频流（默认不复制到 Mac，仅索引与关键片段） | 摄像头本地 |
| NAS | 数据库备份、媒体归档 | 家庭 NAS |
| Local RAG(SQLite + 向量) | 家庭知识、M5 纠错记忆检索 | Mac 本地（复用工厂 RAG） |

视频片段策略：默认只存事件片段（前 15s / 后 30s），原始流留在 microSD（PRD §11.6.6）。

---

## 8. 文件与媒体管理

- 图片/视频/音频本地存储，文件加密（PRD §15.1, §15.3）。
- 音频本地处理或转文本后删除。
- 媒体以 asset_id 独立保存，冲突不覆盖（PRD §7.5）。
- 导出 MD/PDF 由用户主动生成，记录导出时间与导出人（PRD §11.18, §15.4）。
- 大文件不入库，PostgreSQL 仅存元数据与路径。

---

## 9. 多端同步架构

### 9.1 选型（源自 PRD §7.1，Factory-first 复用外部成熟方案，不自研同步）

```text
PowerSync + PostgreSQL(Mac 权威源) + SQLite(安卓)
```

### 9.2 同步与冲突规则（源自 PRD §7.4, §7.5）

- 离线完整可记录，pending_sync 标记，恢复自动补传，禁止丢记录。
- Mac/PostgreSQL 为权威合并源。
- 冲突处理：5 分钟内疑似重复喂奶 → 不自动删，UI 软提示；同事件并发编辑 → 保留版本，最后编辑为当前；离线重复 → 上线合并提示；撤销 → 软删除保审计；媒体冲突 → 按 asset_id 独立保存；医疗/系统规则冲突 → Admin 二次确认并记录版本。
- 首页显示同步状态，每条记录显示记录人。

---

## 10. Baby State Engine 与 Rule Engine

### 10.1 Baby State Engine

- 输入：ObservationEvent 增量。
- 输出：DerivedBabyState（距上次喂奶、24h 奶量/次数、湿/脏尿布数、24h 睡眠、当前会话、24h 最高温、上次用药、活跃告警数、设备健康）。
- 特性：幂等重算、事件驱动增量更新、只派生不告警。

### 10.2 Rule Engine（唯一医疗/阈值/剂量裁决者）

规则域（均通过 EvidencePolicy 版本化）：

- 疫苗规则：中国国家免疫规划 + 自费疫苗衔接，版本化，支持未来更新（PRD §11.12）。
- 用药规则：mg 计算、ml 换算、间隔、24h 上限、月龄禁忌、浓度/体重校验（PRD §11.11.3）。
- 生长规则：WHO 0–5 岁百分位、按性别、趋势提醒（PRD §11.13）。
- 分诊规则：红黄蓝阈值、危险信号、就医建议、3 月龄以下直肠温 38°C 强红线（PRD §11.9, §11.10）。
- 告警阈值规则：喂养/尿布/睡眠趋势的“连续 N 天 / 偏离 X%”双条件（PRD §12.3）。

规则引擎产出必须携带 rule_version / evidence 供审计与追溯（PRD §15.4）。

---

## 11. AI Agent 架构

### 11.1 总体原则（源自 PRD §10.1）

采用分层 Copilot 架构，不横向堆叠“专家 Agent”。工厂 Agent Orchestrator 与 Skill 模式作为工程底座复用。

### 11.2 Agent Orchestrator（源自 PRD §10.2）

职责：判断意图（记录/提问/求助/配置/告警确认）；决定本地或云端模型；注入宝宝上下文与长期记忆；调用 Rule Engine；调度 Domain Copilots；拦截危险输出；输出可追溯建议与轻确认卡片；对任何医疗/用药建议绑定证据链。

### 11.3 Dose Interceptor 剂量拦截器（源自 PRD §10.3）

- 内置于 Orchestrator 输出后置管线。
- 任何 LLM 自由输出中出现具体药量数字（mg/ml/滴）一律拦截。
- 拦截替换为固定安全话术：剂量需医生/药师确认，系统仅在医生已授权且浓度、体重、月龄完整时经 Rule Engine 校验。
- 剂量只能来自 Rule Engine；每次拦截写审计日志（PRD §15.4）。

### 11.4 领域 Copilot（源自 PRD §10.4）

| Copilot | 职责 | 安全等级 | 上线阶段 |
|---|---|---|---|
| Logger Copilot | 自然语言/语音文本→结构化事件、补录、去重、轻确认 | 低 | P0 |
| Proactive Copilot | 喂奶/哄睡/唤醒/补剂/疫苗/体检/发育观察/猛长期预告/趋势预警/晨报 | 低（规则为主） | P0 |
| Vaccine Planner Copilot | 免疫规划、自费疫苗、预约/逾期提醒、接种后观察 | 中（规则版本化） | P0 |
| Growth & Milestone Copilot | 身高体重头围、WHO 曲线、百分位趋势、里程碑清单 | 低 | P0(成长)/V2(里程碑) |
| Family Memory Copilot | 家庭知识结构化、长期记忆读写、纠错沉淀 | 低 | P0 |
| Sleep Session Copilot | 会话起止、夜醒/趴睡/遮脸检测、会话摘要 | 中（影子优先） | P0影子/V2正式 |
| Camera Safety Copilot | 帧采样、ROI、姿态/遮挡/醒来/离床识别 | 中（会话内） | P0影子/V2正式 |
| Jaundice Diary Copilot | 拍摄规范、同位置趋势对比、测胆红素提醒 | 中（不诊断） | P0归档/V1趋势 |
| Health Triage Copilot | 症状分诊、风险等级、危险信号、观察/就医建议、就诊摘要 | 高（需安全审查） | V1 |
| Medication Safety Copilot | 药品识别、浓度/体重校验、间隔/24h/防重复 | 高（规则引擎为主） | P0基础/V1完整 |

所有高/中安全等级 Copilot 输出必须经 Rule Engine 裁决与 Dose Interceptor 过滤。

### 11.5 Prompt System

- Prompt 模板集中管理，采用工厂 Skill 模式（`_factory/skills` 风格）版本化。
- 每个 Copilot 拥有独立 system prompt + 上下文注入契约（明确必注入字段）。
- 医疗类 prompt 强制包含能力边界声明与规则版本占位。
- Prompt 变更纳入 ADR 与文档治理。

### 11.6 Knowledge / Memory

- Knowledge：FamilyKnowledge 结构化 + EvidencePolicy 规则库 + Local RAG 检索（复用工厂 KnowledgeHub / Local RAG）。
- Memory：五层记忆（§6.5），M1/M2/M3/M4 结构化优先，仅 M5 使用少量向量。

### 11.7 Tool Calling 与 MCP

- Orchestrator 通过受控 Tool 接口调用：Rule Engine、Baby State Engine、Memory Store、Notification、Camera/NVR、导出服务。
- 高风险 Tool（用药、告警、云端调用）默认需人工确认或规则前置。
- MCP：本项目默认 `mcp.enabled=false`；如后续引入 MCP，复用工厂 MCP Guard（scanner、schema hash、mode policy、approval、PreToolUse hook），并须新增 ADR。

### 11.8 Model Routing（Factory-first 复用）

```text
Orchestrator → Model Gateway(Smart Proxy 4000, Anthropic-compatible)
             → LiteLLM 4001 或直连本地后端
             → 本地 LLM/VLM(Ollama / llama.cpp / MTPLX)
             → 云端 LLM API（仅当本地不满足且经 Privacy Gateway 脱敏）
```

路由计划由 `models.yaml` + `routing_plans.yaml` 管理（复用工厂双文件模型与路由计划）；本地运行参数由 `model_runtime.yaml` 管理。视频/图片理解走本地 VLM（Camera Safety / Jaundice / 尿布图片识别）。

---

## 12. Camera / NVR 服务

### 12.1 接入（源自 PRD §5.1）

- RTSP：拉流，优先使用子码流供 ANE/VideoToolbox 推理，节省算力。
- ISAPI：订阅硬件级移动侦测/事件报警流，用于唤醒 Mac AI 推理。
- 摄像头具备双向语音，作为告警兜底通道之一。

### 12.2 视频栈（源自 PRD §5.3）

优先 Fregata（Apple Silicon 本地优先，利用 ANE/VideoToolbox）；Frigate 作为开源本地 NVR/Docker 底层备选；ffmpeg 用于拉流、抓帧、片段切片。

### 12.3 分析约束（源自 PRD §11.6.6, §11.7）

- 仅睡眠会话 active 内做行为分析；非会话仅定时抓拍。
- 床区 ROI 由用户手动框定。
- 只做：夜醒候选、遮脸/被褥覆盖、持续趴睡、姿态/离床。
- 不做：全天候行为理解、情绪分析、哭因强判断、呼吸频率监测、医疗级判断、生命体征判断。
- 上线前先跑 7 晚影子模式，误报达标前不开强提醒。

---

## 13. mmWave 设备适配

### 13.1 集成路线（源自 PRD §5.5，MR60BHA2 + XIAO ESP32C6）

- Mac 部署 MQTT Broker（Eclipse Mosquitto，监听 1883）作为家庭物联网数据总线。
- ESP32C6 固件：串口读取雷达帧 → 连接家庭 WiFi → 组装 JSON → PubSubClient 发布。
- Topic：`baby/radar/telemetry`；Payload：presence/state/breathing_rate/heart_rate/abnormal_event/timestamp。
- mmWave Adapter 作为 MQTT Client 订阅，毫秒级拿到数据 → 生成 SensorEvent → 送入 Rule Engine。

### 13.2 定位与约束（源自 PRD §5.4, §11.8, §21.2）

辅助安心层：存在感、呼吸状态、心率趋势、离床、信号丢失。P0 仅预留数据结构/设备类型/SensorEvent/灰色健康告警；V2 正式接入并纳入多信号融合。不单独触发医疗红色告警，不承诺预防 SIDS，不替代成人照护。异常仅提示“辅助监测异常，请人工查看宝宝状态”。

---

## 14. Notification Orchestrator 与告警体系

### 14.1 告警等级（源自 PRD §12.1）

灰色（系统可信度）/ 蓝色（常规提醒，可定时）/ 黄色（关注趋势，非强打扰）/ 橙色（尽快处理，可声音）/ 红色（立即处理，全通道强提醒）。

### 14.2 红色告警原则（源自 PRD §12.2）

高特异；有明确危险信号或多信号一致证据；可追溯依据；不由单一 mmWave 独立触发；不由摄像头单帧触发；用户输入危险症状可直接触发；多信号高置信遮脸可触发。

### 14.3 抗告警疲劳（源自 PRD §12.3）

黄/橙默认“连续 N 天 / 偏离 X%”双条件，阈值可调；趋势类避免单点；影像/雷达高风险默认降一级除非会话内多信号一致；同类黄色 24h 不重复；非红/橙每日合并晨报；每条告警支持反馈并写入 M5 调阈。

### 14.4 送达与升级（源自 PRD §13）

- 多通道：双亲 FCM 高优先级（仅触发信号，详情回连 Mac）+ Mac 客厅扬声器 + App 全屏 Intent + 持续震动响铃。
- 升级：0s 双推 → 60s Mac 重复语音 → 90s 手机加大音量/强震 → 任一确认全停并记录确认人/时间/设备。
- 兜底：手机离线/进程被杀时 Mac 扬声器与摄像头扬声器强制兜底。

### 14.5 安卓告警技术要求（源自 PRD §13.3, §13.4, §21.4）

高优先级通道、IMPORTANCE_HIGH、全屏 Intent、自定义声音/震动、锁屏弹出、本地通知兜底、后台同步、电池/自启白名单引导。生产前预研：Android 14+ 全屏 Intent 权限（USE_FULL_SCREEN_INTENT / canUseFullScreenIntent / ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT）、Doze 与 setExactAndAllowWhileIdle 限制、国产 ROM 杀后台。

---

## 15. API 设计

### 15.1 风格与约定

- REST over HTTPS（家庭局域网内 TLS）；JSON。
- 所有写操作携带同步契约字段（§6.3）。
- 幂等：写接口以 event_id 幂等；重复提交合并。
- 版本前缀 `/api/v1`。

### 15.2 主要 API 域

| 域 | 端点示例 | 说明 |
|---|---|---|
| Auth | `POST /api/v1/auth/login`、`/refresh` | 家庭账号、令牌 |
| Family/User | `GET/POST /api/v1/families`、`/users` | 账号与角色 |
| Baby | `GET/PUT /api/v1/babies/{id}` | 宝宝档案 |
| Events | `POST /api/v1/events`（主要经 PowerSync） | 记录写入 |
| State | `GET /api/v1/babies/{id}/state` | DerivedBabyState |
| Rules | `POST /api/v1/rules/medication/evaluate`、`/triage/evaluate`、`/vaccine/plan`、`/growth/percentile` | Rule Engine |
| Copilot | `POST /api/v1/copilot/query` | Orchestrator 入口 |
| Alerts | `GET/POST /api/v1/alerts`、`/{id}/ack`、`/{id}/feedback` | 告警 |
| Media | `POST /api/v1/media`、`GET /api/v1/media/{asset_id}` | 媒体 |
| Sleep | `POST /api/v1/sleep-sessions`、`/{id}/end` | 睡眠会话 |
| Camera | `GET /api/v1/cameras`、`/{id}/roi`、`/{id}/snapshot` | 摄像头 |
| Sensor | 内部 MQTT → `SensorEvent`（无外部写 API） | mmWave |
| Export | `POST /api/v1/export`（range=7d/30d, format=md/pdf） | 导出 |
| Health | `GET /api/v1/system/health` | 设备/服务健康 |

推送详情不走 FCM，必须由 App 回连 Mac 获取（PRD §15.1, §15.3）。

---

## 16. 外部集成

| 集成 | 协议 | 边界 |
|---|---|---|
| 海康摄像头 | RTSP / ISAPI | 厂商云必须关闭并验证，流量不出局域网 |
| mmWave/ESP32C6 | MQTT(Mosquitto) | 局域网内 |
| Android 推送 | FCM | 仅触发信号 |
| 云端 LLM | HTTPS API | 仅脱敏文本，fallback |
| 独立就医项目 | 跳转接口 + 就诊摘要导出 | 本系统仅保留接口，不做医院/医生推荐 |
| NAS | 网络文件协议 | 备份/归档 |
| 远程访问 | Tailscale / WireGuard | 推荐，默认局域网 |

医院/科室/医生推荐能力移交独立就医项目（PRD §1.4, §2.3）。

---

## 17. 插件与扩展体系

- Copilot 插件化：每个 Domain Copilot 为可插拔单元，注册到 Orchestrator，声明意图匹配、上下文注入契约、安全等级、Tool 权限。
- Rule Pack 插件化：疫苗/用药/生长/分诊/阈值规则以 EvidencePolicy 版本包形式加载，支持热更新与版本回溯。
- Collector/Adapter 插件化：Camera、mmWave、未来传感器以统一 Adapter 接口接入（复用工厂 collector registry 模式）。
- Notification Channel 插件化：FCM、Mac 扬声器、摄像头扬声器、全屏告警为可注册通道。

新增插件遵循工厂原则：最小化、模块化、可复用、与工厂一致，并新增/更新 ADR。

---

## 18. 配置体系

采用工厂配置 SSOT 模式，分层加载：`defaults → 项目配置 → runtime → .env → 环境变量 → CLI`。

| 配置文件 | 内容 | 来源 |
|---|---|---|
| `config/models.yaml` | 模型目录 | 工厂复用 |
| `config/routing_plans.yaml` | 路由计划 | 工厂复用 |
| `config/model_runtime.yaml` | 本地运行参数 | 工厂复用 |
| `config/privacy_policy.yaml` | 脱敏/出站策略 | 工厂复用 |
| `config/alert_thresholds.yaml` | 红黄蓝阈值、双条件参数 | 新增（PRD §12.3） |
| `config/rules/vaccine.yaml` | 疫苗规则库（版本化） | 新增（PRD §11.12） |
| `config/rules/medication.yaml` | 用药规则库（版本化） | 新增（PRD §11.11） |
| `config/rules/growth.yaml` | WHO 生长标准 | 新增（PRD §11.13） |
| `config/rules/triage.yaml` | 分诊规则/红线 | 新增（PRD §11.10） |
| `config/devices.yaml` | 摄像头/mmWave/MQTT 拓扑 | 新增（PRD §4, §5） |
| `config/notification.yaml` | 通道与升级策略 | 新增（PRD §13.2） |

真实密钥仅本地且 gitignored（`.env`、`_infra/.env`），提供 `.env.example`（工厂约定）。

规则库变更必须递增 version 并记录 effective_from/effective_to/source（PRD §8.13, §15.3）。

---

## 19. 权限体系

角色与权限（源自 PRD §3.1, §15.2）：

| 角色 | 权限 | 阶段 |
|---|---|---|
| 父亲/母亲(Admin) | 记录、查看、确认告警、配置规则 | P0 |
| Caregiver | 记录、查看部分状态；不可改医疗/系统规则；不可查看医疗建议 | V2 |
| Viewer | 只读摘要、相册 | V2 |
| System | 自动写入设备/分析/派生/告警事件 | P0 |

- 每个家庭成员独立 user_id。
- 医疗/系统规则变更需 Admin 二次确认并记录变更人、时间、版本。
- 医疗建议对 Caregiver/Viewer 不可见。

---

## 20. 安全体系

- 局域网默认访问；远程走 Tailscale/WireGuard（PRD §15.3）。
- 传输：局域网内 TLS，令牌鉴权。
- 存储：图片/视频/医疗记录本地加密。
- 摄像头厂商云必须关闭并验证流量不出局域网。
- 云端 LLM 仅接收脱敏文本，经 Privacy Gateway 出站管控。
- 操作/审计日志不可删除。
- 高风险动作（用药执行、云端调用、规则变更、红色告警）均需人工确认或规则前置（工厂原则 + PRD 铁律）。

---

## 21. 隐私保护

数据默认策略（源自 PRD §15.1）：

| 数据 | 策略 |
|---|---|
| 视频 | 不上传第三方云，本地 microSD/Mac |
| 图片 | 本地存储，加密 |
| 音频 | 本地处理或转文本后删除 |
| 医疗记录 | 本地加密 |
| 推送内容 | 仅 alert_id/level/type |
| 云端 LLM | 仅脱敏文本 |
| 原始视频流 | 不离开局域网 |
| MD/PDF 导出 | 用户主动生成 |

Privacy Gateway（复用工厂 network privacy 模块：input sanitizer、regex/Presidio/NER 检测、replacer、schema validator、canary）在所有云端调用前执行 PII 脱敏与出站校验。

---

## 22. 可观测性

### 22.1 日志（源自 PRD §22.3）

必须记录：API、同步、告警、设备、AI 调用、剂量拦截、规则引擎执行、用户操作审计、数据导出。审计日志不可删除。

### 22.2 审计（源自 PRD §15.4）

记录：谁创建/编辑/撤销记录、谁确认告警、谁改家庭/医疗规则、告警触发依据、规则版本、LLM 是否被调用、剂量拦截是否触发、导出时间与人。

### 22.3 Metrics

采集使用/价值/安全指标（PRD §20）：单次记录耗时、语音结构化成功率、离线补传成功率、同步延迟、告警误报率、红色告警送达率、设备离线发现时长、剂量拦截成功率等。

### 22.4 Tracing

Orchestrator → Rule Engine → Copilot → Notification 全链路 trace，关联 case/事件/告警 id，用于误报回溯与调阈。

### 22.5 Device Health Monitor（源自 PRD §22.1, §22.2）

监测 Mac 服务、PostgreSQL、PowerSync、摄像头在线/拉流、mmWave、手机同步、NAS/SD 容量、FCM 送达、本地告警链路。摄像头离线 60s 内触发灰色告警；灰色告警不与医疗告警混淆；Today 首页与晨报汇总健康。

---

## 23. 错误处理、Retry、Timeout、Circuit Breaker

- 同步失败：不丢记录，本地保留 pending_sync，指数退避重试直至成功（PRD §7.4）。
- 云端 LLM：超时/失败回退本地模型；本地失败降级为规则-only 输出。
- 摄像头拉流：断线自动重连，连续失败触发灰色告警（PRD §22.2）。
- MQTT：断线重连（MQTT 原生特性）；mmWave 离线触发灰色告警。
- 搜索/外部取数（如启用工厂 network）：复用 EngineCircuitBreaker 与 Tavily/Serper fallback。
- FCM 送达失败：Mac/摄像头扬声器兜底通道保证告警送达。
- 所有外部调用设置 timeout；关键链路（告警送达）以“多通道 + 升级”替代单点重试。

---

## 24. 备份与迁移

### 24.1 备份（源自 PRD §22.4）

- PostgreSQL 定期备份到 NAS。
- 媒体文件 NAS 归档。
- 操作日志不可删除。
- 本地文件加密。
- 恢复流程须在生产前演练（PRD §16.1）。

### 24.2 迁移

- 数据库 Schema 迁移采用版本化 migration 脚本，向前兼容。
- 规则库（EvidencePolicy）以版本记录迁移，保留历史版本用于审计与追溯。
- 文档只放置 SQLite 若临时先文档后代码，进入实现迁移至 `projects/ai-parenting-copilot/`（工厂 §13 建议）。

---

## 25. Deployment

### 25.1 部署拓扑（源自 PRD §4）

- Mac M1 Max 64GB：24h 常驻家庭服务端，运行全部 Mac 侧模块 + Mosquitto + 本地模型后端。
- 安卓 ×2：React Native Android-only 主交互端。
- 摄像头 ×2、mmWave ×1、路由器 ×1。

### 25.2 服务组织

- Mac 侧服务以进程/容器组合部署：SearXNG/Crawl4AI 等 Docker compose（如需联网）、Mosquitto、PostgreSQL、PowerSync Service、应用服务、本地模型后端（MTPLX/llama.cpp/Ollama）+ Smart Proxy/LiteLLM。
- 启动/诊断复用工厂脚本模式（`forge-start.sh`、`model_status.sh`、diagnostics）。

### 25.3 生产前部署清单（源自 PRD §16.1）

创建家庭账号、配置双端、录入宝宝档案、测 FCM、测 Mac 声音告警、接入摄像头与 mmWave、配置 ROI、配置家庭知识库、初始化疫苗/补剂/用药规则、夜间告警演练、离线补传演练、电池/自启白名单、验证摄像头流量不出局域网。

---

## 26. 扩展策略与演进策略

### 26.1 阶段路线（源自 PRD §18）

| 阶段 | 范围 | 关键交付 |
|---|---|---|
| P0（生产前） | 高频、可靠、零误判风险 | 账号权限、双端同步、离线补传、喂养/尿布/补剂/体温/睡眠会话手动、用药记录+间隔+防重复基础、疫苗规则、成长曲线、家庭知识库、Today、晨报、交接摘要基础、告警链路、设备健康、夜间模式、摄像头接入+ROI、mmWave 预留、趴睡/夜醒/遮脸影子模式、黄疸归档、导出基础、母亲健康与辅食数据结构预留 |
| V1 | 0–4 周/1–2 月 | Health Triage、用药安全完整、黄疸趋势、猛长期预告、长期记忆注入、导出完整+就诊摘要、事件片段增强 |
| V2 | 1–3 月 | 摄像头夜醒/趴睡/遮脸正式、睡眠报告、奶量/尿布/睡眠趋势预警、尿布图片识别、母亲健康功能、知识库结构化增强、周/月报、Caregiver/Viewer 上线、mmWave 正式接入 |
| V3 | 3–6 月 | 里程碑清单、活动建议、哭声分类 Beta、成长相册、辅食/过敏数据模型启用 |
| V4 | 6–12 月 | 辅食、过敏原、食物反应时间线、运动发育、更多协作角色 |

### 26.2 P0 可降级项（源自 PRD §18.2）

趴睡仅影子模式；遮脸仅画面异常检测；夜醒仅记录候选；用药仅记录+间隔提醒；黄疸仅归档；睡眠仅手动；导出仅基础统计。

### 26.3 演进原则

- 数据结构在 P0 预留（mmWave/SensorEvent、mother_health、solid_food_log、多 baby_id），后续启用不改动核心表。
- AI 强判断能力后置且以影子模式先行，误报达标才开强提醒。
- 任何架构或模块边界变更须新增 ADR（工厂治理）。
- 新能力优先复用工厂能力，不假设新增基础设施。

---

## 27. 目录结构

```text
projects/ai-parenting-copilot/
├── README.md
├── docs/
│   ├── ARCHITECTURE_FINAL.md        # 本文档
│   ├── ENGINEERING_DESIGN.md
│   ├── TASK_BACKLOG.md
│   ├── PROJECT_STATE.md
│   ├── DEV_LOG.md
│   ├── CHANGELOG.md
│   ├── HANDOFF.md
│   └── ADR/
│       └── ADR-001-*.md
├── server/                          # Mac 服务端
│   ├── gateway/                     # API Gateway + Auth/RBAC
│   ├── sync/                        # PowerSync 集成
│   ├── normalization/
│   ├── state_engine/                # Baby State Engine
│   ├── rule_engine/                 # Rule Engine + rule packs
│   ├── orchestrator/                # Agent Orchestrator + Dose Interceptor
│   ├── copilots/                    # Domain Copilots
│   ├── notification/                # Notification Orchestrator + channels
│   ├── camera/                      # Camera/NVR (Fregata/Frigate/ffmpeg)
│   ├── mmwave/                      # MQTT adapter
│   ├── privacy/                     # Privacy Gateway 适配（复用工厂）
│   ├── memory/                      # 五层记忆 + Local RAG 适配
│   ├── observability/               # log/metric/trace/audit
│   ├── health/                      # Device Health Monitor
│   └── backup/
├── android/                         # React Native Android-only
│   ├── today/ quick_record/ sleep_session/ timeline/ alert_center/
│   ├── sync/ (SQLite + PowerSync client)
│   └── notification/ (FCM + Notifee/native + fullscreen intent + fallback)
├── config/                          # 项目配置 SSOT（见 §18）
├── firmware/esp32c6/                # mmWave 桥接固件
├── tests/                           # unit/integration/security/golden
└── runtime/                         # gitignored 本地运行数据
```

复用工厂能力位于工厂根 `_infra/`、`config/` 中的对应模块（模型路由、Privacy、RAG、Agent/Skill、治理），本项目通过适配层引用，不重复实现。

---

## 28. 关键约束速查（AI Agent 开发须遵守）

1. 记录路径必须离线可用、不丢记录、每条显示记录人。
2. 剂量与医疗阈值只能由 Rule Engine 产出；LLM 输出 mg/ml/滴一律被 Dose Interceptor 拦截。
3. 红/橙告警必须多通道 + Mac/摄像头扬声器本地兜底；红色告警未送达目标为 0。
4. 云端 LLM 只收经 Privacy Gateway 脱敏的文本；视频/图片/音频/原始流不出局域网。
5. 摄像头分析仅睡眠会话内、需 ROI、不做生命体征/呼吸频率；高风险提醒需多信号融合。
6. mmWave 不单独触发红色告警；P0 仅预留，V2 正式接入。
7. 所有规则/医疗变更版本化并记录变更人/时间；审计日志不可删除。
8. 优先复用工厂能力（模型路由、Privacy、RAG、Agent/Skill、治理），新增模块须新增 ADR。

---

## 29. 需求追溯矩阵

| 架构模块 | 来源类型 | 来源 |
|---|---|---|
| 分层架构 / 数据流 | PRD | §6, §17 |
| 数据模型 / 实体 | PRD | §8 |
| 长期记忆五层 | PRD + 工厂(KnowledgeHub/RAG) | §9 / DOSSIER §5.3, 5.4 |
| Baby State Engine | PRD | §6.1, §8.6 |
| Rule Engine / 剂量拦截 | PRD | §10.3, §11.11, §12 |
| Agent Orchestrator / Copilots | PRD + 工厂(Agent/Skill) | §10 / DOSSIER §5.2 |
| Model Routing | 工厂 | DOSSIER §4.2, 5.3 |
| Privacy Gateway | 工厂 | DOSSIER §5.4 network privacy |
| Local RAG / Memory | 工厂 | DOSSIER §5.4, 5.3 |
| MCP Guard（如启用） | 工厂 | DOSSIER §5.4 |
| 多端同步 PowerSync | PRD | §7 |
| Camera/NVR | PRD | §5.1–5.3, §11.6, §11.7 |
| mmWave Adapter / MQTT | PRD | §5.4, §5.5, §11.8 |
| Notification / 告警送达 | PRD | §12, §13 |
| 权限 / RBAC | PRD | §3, §15.2 |
| 安全 / 隐私 | PRD + 工厂(Privacy) | §15, §21 |
| 可观测 / 审计 / 设备健康 | PRD | §15.4, §22 |
| 备份 / 迁移 | PRD | §22.4 |
| 配置 SSOT | 工厂 | DOSSIER §6 |
| ADR / 文档治理 | 工厂 | DOSSIER §5.6, §12 |
| 部署拓扑 | PRD | §4, §16.1 |
| 路线图 / 演进 | PRD | §18, §19 |

---

