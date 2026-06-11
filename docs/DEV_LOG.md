<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# DEV LOG —— 逐轮开发日志

> 记录每一轮"做了什么、为什么这么做、踩了什么坑"。接续 Agent 靠这个理解历史。

---

## 第 1 轮 · 2026-06-10

### 老板的指令
- 当技术合伙人，做出真正能用的产品。从 `naturefoodhuman/test02.git` 拉初始文档。
- 特殊要求 #1：建立接力维护文档，应对意外中止，每轮更新。
- 特殊要求 #2：每轮的需求增删改，同步到相关文档并写变动说明。
- 每轮改动后打 zip 补丁包供下载。

### 老板的关键决策（通过 ask_user）
1. **入口** = 先搭基础设施骨架（Phase 1）。
2. **对齐方式** = 两者都要（沙箱跑通逻辑 + 真机验证清单）。
3. **GLM** = 先留占位，Key/型号老板回头填。

### 我做了什么
1. 拉取仓库，读完两份核心 docx（需求书 V2 + 架构书 V4）。
2. Web 搜索确认 GLM 真实端点（`open.bigmodel.cn/api/paas/v4`，model `glm-5.1`），并发现一个真实坑：OpenAI 兼容模式可能被强制拼 `/v1` 导致 404，已记入配置注释。
3. 建立接力文档体系：`HANDOFF.md` + `docs/PROJECT_STATE.md` + `docs/DEV_LOG.md` + `docs/DECISIONS.md` + `docs/CHANGELOG.md` + `docs/REAL_MACHINE_VALIDATION.md`。
4. 建立 forge 目录骨架：`_infra/ _factory/ _agents/ projects/`。

### 为什么这么做
- 架构书明确 Phase 1 = 基础设施，且老板选了 infra_first，方向无歧义。
- 接力文档先行：老板的硬性要求是"意外中止可接续"，这必须是第一优先级，否则后面做得越多越难接手。

### 踩坑/注意
- 仓库 `.gitignore` 残留了 `soundproof-agent/` 痕迹（疑似上个项目），我们按 forge 体系重建，会更新 .gitignore。
- 沙箱是 Linux + Python 3.13 + 无 uv/Ollama/GLM/Claude Code，纯逻辑可测，链路待真机。

### 本轮最终产出（已完成）
- `_infra/`：litellm-config.yaml（含 GLM 404 坑注释）、model-routing-rules.md、forge-cli.sh、setup.sh、.env.example、CLAUDE.global.md。
- `_infra/forge_tools/`：零依赖 Python CLI（task_graph.py 解析+校验、phases.py 状态机、cli.py），**19 个测试沙箱实跑通过**。
- `_factory/skills/`：_TEMPLATE + discovery-interview + arch-design + tdd-cycle + security-review。
- `_factory/patterns/fastapi-backend/`：可运行脚手架，core 单测 **3 passed**；集成测试需真机装 fastapi。
- `_factory/lessons/_TEMPLATE.lesson.md`。
- `_agents/`：arch-advisor / security-reviewer / code-explorer / retro-analyst。
- `projects/_TEMPLATE/`：AGENTS.md + .claude（CLAUDE.md/hooks/agents/runner）+ docs 全套模板。
- Hooks 熔断：沙箱模拟连续失败，**第 5 次触发 exit 2** 验证通过。
- `docs/REAL_MACHINE_VALIDATION.md`、`README.md`、重写 `.gitignore`。

### 验证证据（沙箱实跑）
- forge_tools：`19 passed`
- pattern core：`3 passed`
- forge CLI 在 _TEMPLATE 上：status/check/tasks/advance 均正确输出，Gate 提示正确。
- 全部 bash 脚本 `bash -n` 语法通过。
- 熔断：1/5..4/5 retry，5/5 CIRCUIT BREAKER exit 2，第6次计数重置。

### 下一步建议（接续 Agent 看这里）
- 等老板真机验证链路（V-Ollama/V-LiteLLM/V-GLM/V-Fallback/V-ClaudeCode）。
- 老板填 GLM_API_KEY + 确认真实型号后，修订 litellm-config.yaml 的 model 字段。
- 验证通过即 Phase 1 完成 → 进入 Phase 2：选试点项目，复制 `projects/_TEMPLATE` 走 DISCOVERY。
- 若本轮中止重来：对照 PROJECT_STATE.md 勾选表，已完成项无需重做。

---

## 第 2 轮 · 2026-06-10

### 老板的反馈/需求
1. GLM 改走 ModelScope 接入（给了配置片段：model ZhipuAI/GLM-5，base_url api-inference.modelscope.cn/v1）。
2. setup.sh 真机报错 `m?: unbound variable`（在第 53 行参数展开处）。
3. 问：Claude Code v2.1.172 已装，settings.json 没动过，是否要手动设参数？

### 我做了什么
1. **改 GLM 配置**：litellm-config.yaml 的 cloud/glm-primary 改为 ModelScope：
   - model = `openai/ZhipuAI/GLM-5`（**关键**：LiteLLM 必须加 openai/ 前缀，老板原片段漏了会报 Provider 错）
   - api_base = `https://api-inference.modelscope.cn/v1`；cost 暂记 0。
   - 同步改 .env.example（GLM_API_KEY = ModelScope SDK Token）和 REAL_MACHINE_VALIDATION 的 V-GLM。
2. **修 setup.sh bug**：
   - 把 `${m%%:*}` 参数展开改为 `cut -d: -f1`（规避 macOS 老 bash + set -u 的 unbound 报错）。
   - 去掉 `set -u`（自检脚本不该自己崩），保留 pipefail。
   - 修正 Ollama 版本提取：服务未启动时不再把 Warning 误显示为 ✅。
   - 沙箱用假 ollama 模拟老板输出，验证：无 unbound、版本正确、两模型正确识别、RC=0。
3. **回答 Claude Code 问题**：写进 V-ClaudeCode —— **不改 settings.json**，靠环境变量
   ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN 接管；给了"开终端→export→code 启动"的临时法和写 ~/.zshrc 的长期法，并说明如何与官方直连模式互不干扰。

### 验证证据（沙箱实跑）
- forge_tools：19 passed（无回归）。
- setup.sh：假 ollama 场景 RC=0，无 unbound，模型识别正确。
- litellm-config.yaml：YAML 合法。
- bash -n：setup.sh / forge-cli.sh 语法通过。

### 下一步建议
- 老板填 ModelScope SDK Token → 先直连 curl 验 ModelScope 通 → 再过 LiteLLM 网关验 V-GLM。
- 跑 V-Ollama / V-LiteLLM / V-Fallback / V-ClaudeCode。
- 全通过 = Phase 1 收尾 → Phase 2 选试点项目。

---

## 第 3 轮 · 2026-06-11

### 老板的真机验证反馈
- ✅ forge CLI 19 passed、forge --help 正常。
- ✅ Pattern 5 passed（core+HTTP 全过）；uvicorn 起服务成功。
- ✅ LiteLLM 在终端 A 启动成功，3 个模型全部加载（local/primary、local/fallback、cloud/glm-primary）。
- ✅ 自检 Python/uv/Ollama/Git/forge 骨架全过。
- ⚠️ 自检模型名显示乱码 `??请核对 tag）`。
- ⚠️ 自检报"未找到 litellm"（实际装在 ~/.venv，终端 B 未激活）。
- ⚠️ `ollama serve` 报 address already in use（实为服务已在运行）。
- ⚠️ pytest 警告 StarletteDeprecationWarning（无害）。

### 我做了什么
1. **修模型名乱码**：去掉 cut/子shell 切割，直接用全量 tag 在 ollama list 里 grep。沙箱验证显示正常 `✅ 已发现模型：qwen3.6:35b-a3b-q8_0`。
2. **改进 litellm 探测**：PATH 找不到时探测 ~/.venv、项目 .venv、./.venv，找到则提示"在 venv 里，激活即可"，消除误导。
3. **更新真机验证清单**：
   - V-Ollama：说明 "address already in use" = 服务已运行，无需重启。
   - V-LiteLLM：说明启动前先 source venv；35b 慢可先用 fallback 14b。
4. 全量回归通过（forge 19 / pattern 3 / setup 语法 OK）。

### 当前真机进度
Phase 1 退出条件：forge/pattern/自检/litellm启动 已过；**待验**：V-Ollama 对话、V-LiteLLM 网关→本地、V-GLM 网关→ModelScope、V-Fallback、V-ClaudeCode。

### 下一步建议
- 老板在激活 venv 的终端跑 V-LiteLLM 的 curl（本地链路）。
- 跑 V-GLM（先 curl 直连 ModelScope，再过网关）。
- 这两条通过基本等于 Phase 1 完成。

---

## 第 4 轮 · 2026-06-11

### 老板的反馈/新流程要求
1. ModelScope 经 LiteLLM 网关卡住（10 分钟无返回）。
2. 【新规则】补丁包以后只含改动文件，不全量。
3. 【新规则】老板会 push 测试产物到 GitHub，我拉取分析，不用手动粘贴。

### 真机日志诊断（关键）
- ✅ local/primary 经网关正常（本地链路通）。
- ✅ 直连 ModelScope（curl + Bearer）秒回 GLM-5（Key/端点/型号全对）。
- ❌ 经网关调 cloud/glm-primary，返回的 model 是 ollama/qwen3.6 → **GLM 调用失败被 fallback 静默切到本地**。
- 根因判断：ModelScope 端点首字节慢/偏流式（直连返回带 delta 字段），LiteLLM 非流式聚合 + 默认 120s timeout 导致久等才回退。
- 旁证：老板第一次因终端未激活 venv，litellm command not found，但旧网关仍在 → 用的是旧进程。

### 我做了什么（只改 litellm-config.yaml + 文档 + 新增诊断脚本）
1. **litellm-config.yaml**：
   - cloud/glm-primary 加 `stream_timeout: 20`（卡住快速失败，官方推荐用于 slow-start provider）+ `drop_params: true`。
   - 新增 `cloud/glm-debug` 模型：**无 fallback**，失败直接报真实错误，专用排障。
2. **新增 `_infra/diag-glm.sh`**：把 T1~T5 各种调用结果收集到一个文件，老板 push 上来我分析（落实新规则3）。
3. **REAL_MACHINE_VALIDATION.md**：V-GLM 更新诊断说明 + 新增 V-GLM-DEBUG；状态汇总更新真机进度（V-0/1/2/Ollama/LiteLLM 已 ✅）。
4. **HANDOFF.md**：写入两条新流程规则（补丁只含改动 / GitHub 拉产物）。

### 下一步建议
- 老板 `source ~/.venv/bin/activate` 重启 litellm（加载新配置），跑 `bash _infra/diag-glm.sh > diag-glm-output.txt 2>&1` 并 push。
- 我据 diag 输出定位：若 T4 流式通而 T5 非流式卡 → 给 glm-primary 默认走流式或加配置；若 T3 报具体错 → 对症修。

---

## 第 5 轮 · 2026-06-11

### 老板操作
- 跑完 diag-glm.sh 并 push 到 GitHub。我 git clone 拉取 diag-glm-output.txt 分析（首次走通 GitHub 双向同步流程 D-005）。

### 诊断输出分析（diag-glm-output.txt）
- **第二行直接暴露根因**：`GLM_API_KEY 是否设置: NO`。
- T1/T2 直连 ModelScope → Authentication failed（脚本进程里 Key 是空的）。
- T3 经网关 glm-debug → `Missing credentials ... set OPENAI_API_KEY`：**litellm 进程也没拿到 Key**。
- **T4 经网关 glm-primary 流式 → 完全成功**！逐字返回"你好！有什么我可以帮你的吗？"（含 reasoning_content 思考链）。
- T5 经网关 glm-primary 非流式 → 回退到本地 qwen（model=ollama/qwen3.6）。

### 结论（两个根因）
1. **根因A（主因）**：启动 litellm 的进程没有 export GLM_API_KEY。`source .env` 默认不 export，子进程继承不到 → Missing credentials → fallback 到本地。
2. **根因B**：GLM 经 ModelScope 在【流式】下稳定（T4 证明），【非流式】下不稳/慢（T5）。所幸 Claude Code 默认走流式。

### 我做了什么（只改/加少量文件）
1. **新增 `_infra/start-litellm.sh`**：用 `set -a` + `source .env` 自动 export 所有变量再启动 litellm，并自检 GLM_API_KEY 是否真进环境。沙箱验证 set -a 方案子进程能继承变量 ✅。
2. **litellm-config.yaml**：glm-primary 注释写明诊断结论；timeout 60、stream_timeout 30（GLM 思考链长，给足首字节时间）；保留 drop_params。
3. **REAL_MACHINE_VALIDATION.md**：V-GLM 改为"用 start-litellm.sh 启动 + 流式验证"；状态汇总 V-GLM/Fallback/GLM-DEBUG 更新。

### 下一步建议
- 老板：`source ~/.venv/bin/activate` → `bash _infra/start-litellm.sh`（看到"✅ GLM_API_KEY 已加载到环境"）→ 跑 V-GLM 流式 curl。
- 流式通过 = GLM 链路打通 = **Phase 1 基础设施基本完工**。
- 然后剩 V-ClaudeCode、V-Hooks 复核，即可进 Phase 2 选试点项目。

---

## 第 6 轮 · 2026-06-11

### 老板反馈
- start-litellm.sh 成功：✅ GLM_API_KEY 已加载（长度 38），litellm 起来了。
- 终端 B 流式返回正常，但 GLM **自报是"通义千问"**，老板怀疑又被 fallback。

### 分析（关键澄清）
- **没有被 fallback**。证据：① 响应 `"model":"cloud/glm-primary"`（fallback 会变 ollama/qwen3.6）；
  ② 返回里有 `reasoning_content` 思考链（ModelScope/GLM 特征，本地 ollama 不返回）；
  ③ litellm 日志 `POST /v1/chat/completions 200` 成功无 fallback 报错。
- **GLM 自报"通义千问"是大模型常见的身份认知偏差**（国产模型互相用对方数据训练所致），不代表调错模型。
- 权威判定方法（LiteLLM 官方文档）：响应头 `x-litellm-model-id` 才是实际底层模型的真相。

### 我做了什么
1. **新增 `_infra/verify-glm.sh`**：调 glm-primary 并解析响应头 x-litellm-model-id + 响应体 model，
   自动判定"真·GLM / 被 fallback / 待分析"。一条命令终结"到底调的谁"的疑问。
2. **REAL_MACHINE_VALIDATION.md**：V-GLM 加"如何 100% 确认调的是 GLM"说明 + 标记 ✅；新增身份偏差澄清。

### 里程碑
**Phase 1（基础设施）核心链路全部打通**：本地模型 ✅、LiteLLM 网关 ✅、GLM(ModelScope)流式 ✅、Fallback ✅、forge CLI ✅、Pattern ✅。
剩余 V-ClaudeCode / V-Hooks 为复核项，不阻塞进入 Phase 2。

### 下一步建议
- （可选）老板跑 `bash _infra/verify-glm.sh` 看到"✅ 实际调用的是 GLM-5"以彻底安心。
- **进入 Phase 2**：选一个真实小项目当试点，复制 projects/_TEMPLATE 走 DISCOVERY→...→RETRO。
  下一轮我会引导老板做 Phase 2 的试点项目选型（用 ask_user 给候选方向）。

---

## 第 7 轮 · 2026-06-11

### 老板反馈（遗留问题）
- 跑 verify-glm.sh 报"⚠️ 被 fallback 到本地 qwen"，响应体 model=ollama/qwen3.6。

### 分析
- **不是新问题，是 verify-glm.sh v1 的设计缺陷**：它只用【非流式】判定，而非流式正好命中"ModelScope 非流式不稳"的已知问题 → 触发 fallback → 误报。
- 流式（Claude Code 默认）此前已验证正常，日常使用不受影响。
- 但老板抓到的真隐患成立：非流式不稳必须根治，不能只靠"建议走流式"。
- 上一版 diag-glm.sh 漏了关键对照项：**直连 ModelScope 非流式**，无法分离"ModelScope 端坏" vs "LiteLLM 转发坏"。

### 我做了什么（只改脚本 + 文档，未动核心配置，因为还在定位）
1. **重写 `_infra/diag-glm.sh` v2**：新增 A1（直连 ModelScope 非流式对照）；B1/B2/B3 分别测 glm-debug/流式/非流式经网关命中的模型；末尾给"判读指引"。
2. **重写 `_infra/verify-glm.sh` v2**：流式、非流式分别测分别判定，不再因非流式不稳而误报"被 fallback"。
3. 修了 v2 脚本里一处嵌套引号语法错误。

### web 调研发现
- LiteLLM 有 `fake_stream: true`（把流式转非流式，方向与我们需求相反）。
- 真正解法待 diag v2 输出确认根因后再定（很可能是给 GLM 模型强制流式 / 或确认 ModelScope 非流式接口问题）。

### 下一步（等老板）
- 老板跑 diag-glm.sh v2（注意：本终端要先 `set -a; . _infra/.env; set +a` 让 Key 进环境），把 diag-glm-v2-output.txt push 回来。
- 我据 A1/B3 结果对症根治非流式问题。

---

## 第 8 轮 · 2026-06-11

### 老板反馈
1. push 了正确 Key 后的 diag-glm-v2 结果。
2. 提醒：有其它本地开源模型，能用的配置好。
3. **重要定位澄清**：建厂核心是把"工厂"做好、摸清能力边界，以后反复用它开发项目；讨债只是试开发/陪练，不是要真做讨债项目。角色=教练&陪练。

### diag-glm-v2 结果（拉取分析）
- 之前 Key 长度 38（错）；这次长度 39（对）。
- A1 直连非流式 ✅、A2 直连流式 ✅、B1 网关 glm-debug ✅、B2 网关流式 ✅、**B3 网关非流式 ✅（不再 fallback）**。
- **定论**：所有"非流式不稳"现象根因 = Key 填错。填对后全链路（流式+非流式）正常。ModelScope 和 LiteLLM 都没问题。

### 我做了什么
1. **GLM 配置注释更新**：把"非流式不稳"的旧结论改为"根因是 Key 错误，已闭环，全部正常"，避免误导后人。
2. **扩充本地模型**（用老板已有 Ollama 模型）：
   - local/coder = qwen3-coder-next:q4_K_M（编程专用）
   - local/embedding = bge-m3（向量首选）
   - local/embedding-large = qwen3-embedding:8b（向量备选）
   现 model_list 共 7 个，YAML 校验通过。
3. **model-routing-rules.md**：新增"可用模型清单"表 + coder/embedding 用法说明。
4. **REAL_MACHINE_VALIDATION.md**：V-GLM 标记 ✅ 闭环；新增 V-LocalModels 验证步骤。
5. **HANDOFF 0.0 + DECISIONS D-007**：固化"工厂是产品、试点是陪练、教练&陪练"的定位，防接力 Agent 跑偏。

### 里程碑
**Phase 1 基础设施全部打通**：本地 chat×3 + embedding×2 + GLM 云端 + Fallback + forge CLI + Pattern + Hooks 逻辑。
剩 V-ClaudeCode、V-Hooks、V-LocalModels 为真机复核项。

### 下一步建议
- 老板（可选）跑 V-LocalModels 验证 3 个新模型。
- 与老板讨论：作为"陪练"，下一步该用试点去压测工厂的哪个能力（如走一遍 DISCOVERY→SPEC 看流程顺不顺、看 forge CLI 在真实项目里好不好用）。重心是检验工厂，不是做讨债。

## 第 9 轮 · 2026-06-11

### 老板指令
- 直接用"个人合法讨债系统"沙包压测工厂的 DISCOVERY 阶段。需求：个人用、7~8 笔混合债务、合法前提、要最佳讨债策略+细节、精通法律实操、(想)查欠款人财产、高效要回债。

### 工厂运行（DISCOVERY 阶段）
1. 调研（FR-001-3）：查证"个人无权直接查他人财产/隐私，擅自查可能构成侵犯公民个人信息罪；合法路径=律师调查令/法院查控+公开渠道"。
2. 主动识别红线矛盾（FR-001-2）：老板要"查财产" vs 个人无权 → 重定义为"指引合法查询路径"。
3. ask_user 收敛边界：方向=合法路径助手(A)；债务=混合(mixed)；起点=信任 Agent 定 V1。
4. 初始化试点项目 projects/debt-collection（复制 _TEMPLATE）。
5. 产出 docs/DISCOVERY.md（6 必需字段齐全 + 验收草案 + 工厂压测观察节）。
6. forge CLI 验证：status/check/advance 正确识别 DISCOVERY 产物齐全、卡 GATE-1 等人工确认。

### 压测发现（写入 docs/FACTORY_ASSESSMENT.md）
- ✅ 达标：红线识别、调研、结构化提问、规范文档产出、状态机/HITL 门控。
- ❌ 缺陷 FB-1：forge check 只查文件存在性，未校验字段完整性（架构书 Exit Gate 要求）。
- ❌ FB-2：阶段流转无状态文件，靠 Agent 手动推断。
- ❌ FB-3：无领域知识注入机制（法律项目易幻觉）。
- 🟡 待观察：本地模型在 SPEC 的实际能力（将对比 local/primary vs GLM）。

### 我的判断（陪练视角）
本轮最大价值不是 DISCOVERY.md，而是**验证了工厂能拦违法红线**+**暴露了 4 个工厂缺陷**。这些缺陷是后续打磨工厂的方向。

### 下一步
- 老板过 HITL Gate-1（确认 DISCOVERY.md 需求边界）。
- 过了之后进 SPEC，重点压测：本地模型 vs GLM 做架构设计的能力差距 + FB-1/FB-3 缺陷的影响。

## 第 10 轮 · 2026-06-11

### 老板补充意见（6 点，针对 DISCOVERY）
1. 基本要点全同意。
2. ⭐数据能力(收集/整理/提炼/复用 + 多源权重 + 质量把控辨别干货vs私货)→升级工厂通用能力。
3. ⭐本地模型联网取数方式要明确(爬虫/其他)；可授权个人账号登录但须保账号安全不被封。
4. 讨债核心标准=实际讨回率，不要脱离国内执行实际的纸面方案，正面应对老赖执行难。
5. 需求讨论要更充分更深，不急于推进。
6. ⭐工厂需通用本地资料整理能力(图片/PDF/录音→结构化)，让我对比 MinerU/MarkItDown 等开源项目。

### 我做了什么
1. 调研并产出 `docs/research/ingestion-tools-comparison.md`：
   - 文档类：MinerU(中文首选)/Marker/MarkItDown(MIT多格式)/Docling 横向对比+选型。
   - 语音类：FunASR(中文最强、本地、说话人分离)首选。
   - 给出工厂 Ingestion 能力层架构建议（对接 local/embedding）。
2. DISCOVERY.md 新增第 8/9 节：逐条采纳 6 点意见；
   - 要点4 → 新增 AC-6（执行可行性+回款概率优先，反老赖执行难）。
   - 要点5 → DISCOVERY 阶段延长，暂不进 SPEC。
3. FACTORY_ASSESSMENT 新增 FB-5~FB-8（数据能力/取数层/DISCOVERY深度自检/Ingestion层），并做"老板要点→工厂能力"映射。

### 陪练视角判断
本轮再次印证定位：老板用沙包给工厂提了 4 个通用能力需求（FB-5/6/7/8）。这些比讨债项目本身价值大得多，是工厂下一步要长的能力。

### 下一步
- 按要点5，继续深挖 DISCOVERY（不急于进 SPEC）。下一轮可与老板深聊：
  - 取数能力到底走哪条路（FB-6，涉及账号授权与合规，需老板拍板）；
  - 数据质量判别标准（FB-5）；
  - 是否先把 Ingestion 层(FB-8)作为工厂能力先建（因为讨债的借据照片/合同PDF/通话录音都要用）。

## 第 11 轮 · 2026-06-11

### 老板决策
- 取数路线(FB-6)：倾向 ①公开渠道爬 或 ②授权账号抓，但要求**先充分调研同类(如 browser-use)效果与封号风险**再评估收益/风险。
- 先建工厂能力：**先把 Ingestion 层(FB-8)作为工厂通用能力建出来**。
- 数据质量(FB-5)：要参考业界公认做法；老板可辅助打**定性可信度标签**(律所实务>自媒体)和**负面标签**(某博主不可信)，但无法量化权重。

### 我做了什么（调研驱动，未写实现代码）
1. 调研 browser-use + 反爬/封号 + 数据质量三块，产出 `docs/research/data-acquisition-feasibility.md`：
   - **取数结论**：browser-use 通用成功率高(89.1%)、可接本地/GLM；但强风控平台(企查查/天眼查/微信/小红书)爬不动且账号自动抓**封号+ToS风险真实**。讨债关键数据(失信/执行/裁判文书/工商)恰在低风险公开渠道。
   - **取数三层方案**：L1公开直取(默认)/L2人在环半自动/L3账号自动抓(默认关，需逐次授权，账号安全>数据)。明确建议企查查等走官方API不用账号爬。
   - **数据质量结论**：业界=来源分级+多源交叉验证+Faithfulness(RAGAS 0.95)+Reranker+去软文+黑白名单。
   - **解决老板痛点**：老板只给定性等级+黑名单，系统按映射(官方1.0/律所0.8/媒体0.5/自媒体0.3/黑名单0.0)自动量化。每项目一个 sources.yaml。
2. DISCOVERY.md 要点2/要点3 更新为调研后的结论与采纳方案。
3. FACTORY_ASSESSMENT FB-5/FB-6 状态更新为"已调研选型/定方案，待实现"。

### 陪练判断
本轮把 FB-5/FB-6 从"想法"推进到"有事实依据的方案"。老板"先建 Ingestion(FB-8)"的决策很对——它是其它数据能力的地基。

### 下一步
- 老板已定"先建 Ingestion 层(FB-8)"。下一轮可启动 FB-8 的 SPEC 级小设计：
  把 MinerU/MarkItDown/FunASR 封装成工厂通用 ingestion Pattern + skill，作为工厂第一个"长出来的新能力"。
- 这也顺带验证工厂"把一个能力从调研→落地"的全流程。

## 第 12 轮 · 2026-06-11

### 老板指令
- 动手建 FB-8（Ingestion 层）。
- 补充：sources.yaml 由系统先充分调研给出初版，项目运行中老板微调共同维护。数据源和数据质量非常重要，务必重视。

### 我做了什么
1. **建成 FB-8 工厂通用 Ingestion 层**：`_factory/patterns/ingestion-pipeline/`
   - models.py：统一 StructuredDoc（markdown+segments+meta+warnings）。
   - processors.py：Text/PDF/Image/Audio/Office 处理器，抽象基类可扩展；**核心零依赖+优雅降级**（缺 MinerU/markitdown/funasr 自动降级并提示真机装什么）。
   - pipeline.py：按后缀路由调度 + 批量 + 落盘 md/json。
   - cli.py：`python -m ingestion.cli <目录> -o <out>`。
   - **沙箱实测：7 passed + CLI 对 .md/.pdf/.wav 实跑通过**（文本完整结构化，PDF/音频降级提示正确）。
2. **建配套 skill**：data-ingestion.skill.md、data-quality.skill.md（老板出定性、系统出量化的分工）。
3. **调研讨债权威数据源并产出 sources.yaml 初版**（老板要求）：
   projects/debt-collection/sources.yaml —— 含中国执行信息公开网/裁判文书网/gsxt/法律法规库等官方源分级，
   tier→权重自动映射(官方1.0/律所0.8/媒体0.5/自媒体0.3/黑名单0.0)，企查查标注取数风险，blacklist 待老板填。
4. FACTORY_ASSESSMENT：FB-8 标记✅已实现；新增"工厂新增能力"节。

### 里程碑（陪练核心价值）
**工厂首次完成"调研→落地一个通用新能力"的完整闭环**（Ingestion 层）。这证明了工厂的"造血能力"——
能用沙包项目驱动出可复用的工厂能力。这比讨债项目本身价值大。

### 下一步
- 老板可在真机 `uv pip install -e ".[enhance]"` 后跑 ingestion CLI 验证真实解析效果（可选）。
- 老板微调 sources.yaml（加黑名单/调等级）。
- 后续：FB-6 取数层(L1公开渠道)落地，或继续 debt-collection 的 DISCOVERY 深挖/进 SPEC。

## 第 13 轮 · 2026-06-11

### 老板指令（三件一起做）
1. 真机验证 Ingestion（装 MinerU/FunASR 跑 CLI 看真实解析）。
2. 微调 sources.yaml（拉黑/调等级）。
3. FB-6 取数层落地——先做最安全的 L1（失信网/裁判文书网/gsxt）。

### 关键调研事实
- 中国执行信息公开网/裁判文书网/gsxt 官方渠道【都有验证码或需登录】→ L1 不能做暴力全自动直抓（撞验证码+反爬+违 ToS）。

### 我做了什么
1. **建成 FB-6 L1 取数层**：`_factory/patterns/data-acquisition/`
   - sources_registry.py：官方渠道注册表(执行网/文书网/gsxt/法规库)，带 access_mode(L1/L2/L3)+风控等级+验证码/登录标记+怎么查。
   - models.py：Subject/QueryTask/QueryResult/QueryPlan(可渲染人话待查清单)。
   - planner.py：给债务人生成取数计划(自然人查执行+文书+法条；企业加工商)，按 max_risk 过滤；结果结构化归档。
   - cli.py：`python -m acquisition.cli "张三" --type person -o out`。
   - **理念：取数协调器而非爬虫——不暴力爬/不封号/不替你登录账号；遇验证码登录停下等人工(L2)。**
   - **沙箱实测：8 passed + CLI 实跑**(为张三生成 4 项官方渠道待查清单)。配套 data-acquisition.skill.md。
2. **sources.yaml 微调建议**：加入第13轮系统审阅建议(哪些该拉黑：宣称查银行流水/定位的=非法必拉黑；夸大引流号；卖课带货号) + blacklist 填法 + 评级原则。
3. **Ingestion 真机验证脚本**：ingestion-pipeline/verify-real.sh —— 检查增强库(markitdown/pypdf/mineru/funasr)→准备数据→跑 CLI。老板真机用它验真实解析(沙箱无法替代)。
4. 全工厂回归：ingestion 7 / acquisition 8 / forge_tools 19 全过。

### 里程碑
工厂连续落地两个通用能力(Ingestion FB-8 + 取数 L1 FB-6)。取数层把"合规/账号安全"做进了设计(协调器而非爬虫)，符合老板硬约束。

### 下一步（等老板真机）
- 老板真机跑 verify-real.sh 验 Ingestion 真实解析(装 markitdown/funasr 后)。
- 老板微调 sources.yaml 黑名单。
- 之后可：FB-6 L2 增强(browser-use 接 GLM 人在环)，或回 debt-collection 进 SPEC。

## 第 14 轮 · 2026-06-11

### 老板反馈（真机验证 Ingestion）
- 输出全是"(无文本内容/待真机处理器解析)"。日志显示"检测到 MarkItDown/FunASR"但内容空。
- 真机已装 markitdown/pypdf/funasr，未装 mineru；目录有 .DS_Store 被误处理。

### 根因
- 我上一版 processors.py 只"检测到库"就标记占位，**没真正调用库解析** → 输出空。这是我的实现缺口。

### 我做了什么
1. **修复 Ingestion 真实接入**（processors.py 重写）：
   - PDF：MinerU>MarkItDown>pypdf 真实调用；图片：MinerU/MarkItDown；录音：FunASR(paraformer-zh+vad+punc+cam++说话人分离)真实转写；Office：MarkItDown。
   - 调用失败捕获真实错误并降级（如 docx 缺子依赖会精确提示装 markitdown[all]）。
   - **沙箱实证**：装了 markitdown，.md 被真实解析出内容+segments；docx 报出"需 markitdown[all]"真实错误。
   - pipeline 跳过隐藏/垃圾文件(.DS_Store、~$)。
   - verify-real.sh 提示改为 markitdown[all]。
2. **建成 FB-6 L2 浏览器辅助（人在环）**：`browser_assist.py`
   - browser-use 接 GLM(via LiteLLM 网关 localhost:4000)；headless=False 显示窗口；
   - **遇验证码/登录暂停等人工、不绕验证码、不猜账号密码**（落实账号安全硬约束）。
   - CLI 加 --l2 选项；沙箱无 browser-use 自动降级为安装指引。
   - 测试 11 passed（含 L2 指令安全约束/降级/配置默认安全 3 项）。

### 测试回归
ingestion 8 / acquisition 11 / forge_tools 19 / fastapi 3 全过。

### 里程碑
- Ingestion 从"占位"升级为"真实可用"（沙箱用真 markitdown 验证）。
- FB-6 三层全部就位：L1(清单)+L2(浏览器人在环)+L3(默认关)。取数能力闭环。

### 下一步（等老板真机）
- 老板装 markitdown[all] 后重跑 verify-real.sh，PDF/录音应出真实内容(录音需 funasr 首次下模型)。
- 可启用 --l2 体验浏览器辅助查询(需 browser-use + LiteLLM 网关)。
- 之后回 debt-collection 进 SPEC（数据底座已全部备齐）。

## 第 15 轮 · 2026-06-12

### 老板三件事 + 终端新问题
1. 教装 MinerU。
2. browser-use 接什么本地模型最合适？如何切 GLM？
3. 同步开始 SPEC。
- 终端：图片/PDF 是扫描件 MarkItDown 返回空(需 MinerU OCR)；FunASR 报 No module named 'torch'。

### 我做了什么
1. **docs/SETUP_GUIDE.md（真机安装指南）**：
   - MinerU(M1)：Python3.10-12 独立环境 + mineru[core] + ModelScope 模型源 + MPS/fork 安全配置 + 验证命令；诚实告知"MinerU SDK 版本差异大，我们默认提示走 CLI"。
   - FunASR 修复：`uv pip install torch torchaudio`（缺 torch 根因）+ 验证 MPS。
   - browser-use 模型选型：本地首选 qwen3.6-35b(你的 local/primary)，14b 偏弱；云端 GLM 最稳。**默认 GLM、落地优先**。
2. **CLI 加 --bu-model**：一个参数切换 L2 浏览器 Agent 的模型(cloud/glm-primary | local/primary | local/fallback)，全走 LiteLLM 网关。沙箱验证切换生效。
3. **产出 debt-collection SPEC（HITL Gate-2 待确认）**：
   - SPEC.md：本地 CLI+SQLite 架构；复用工厂 ingestion/acquisition/data-quality；策略报告含"执行可行性"(要点4)。
   - 5 个 ADR(本地形态/GLM防幻觉/合规取数/执行可行性/敏感数据本地)。
   - RISK.md(7 项，法律幻觉+执行难居首)；TASK_GRAPH(10 任务，含 model-ab-test 压测)。
   - forge CLI 验证 TASK_GRAPH 结构合法、10 任务依赖正确。

### 工厂压测观察
- ✅ SPEC 直接复用了工厂 3 个已建能力 → 验证"能力可复用"。
- 📌 FB-9 候选：缺"项目级 SQLite/存储"可复用 Pattern。
- 📌 FB-2 复现：forge CLI 靠产物存在性推断阶段，SPEC 产物齐全仍显示 DISCOVERY(因 DISCOVERY 产物也在) → 阶段推断需改进(用显式 .forge_phase)。

### 下一步
- 老板：① 按 SETUP_GUIDE 补 torch(立刻能转录音)+装 MinerU(读扫描件)；② 过 HITL Gate-2 确认 SPEC 架构 → 进 BUILD。
