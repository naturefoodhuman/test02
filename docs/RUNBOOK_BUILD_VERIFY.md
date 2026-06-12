<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 02:10:00 CST
-->

# RUNBOOK —— 真机验证 BUILD（保姆级，逐步）

> 给老板的逐步操作手册。**每一步都写清：哪个终端、cd 哪里、虚拟环境激活没、预期输出、出错怎么办。**
> 你的项目根（下称 `项目根`）：`/Users/naturist/MusicProject/AI-Project-Incubation-Factory`

---

## 准备：先确认你在哪、环境是什么

打开"终端"App。先认识两个概念：
- **提示符**：行首那串字。没激活虚拟环境时像 `naturist@... %`；激活后**前面会多一个括号名**，如 `(.venv) naturist@... %`。
- **激活虚拟环境** = 运行 `source <某个venv>/bin/activate`；**退出**用 `deactivate`。

---

## 任务一：验证 BUILD（应 18 passed）

### 步骤 1（终端A）：进入项目、激活你的主 venv
```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
source ~/.venv/bin/activate
```
- ✅ 预期：提示符变成 `(.venv) naturist@... %` 或 `(naturist) ...`（取决于你的 venv 名）。
- ❓ 若提示 `source: no such file`：说明你的 venv 不在 `~/.venv`。先 `ls ~/.venv/bin/activate` 确认路径；找不到就告诉我你的 venv 在哪。

### 步骤 2（终端A）：进入试点项目目录
```bash
cd projects/debt-collection
pwd
```
- ✅ 预期：`pwd` 显示 `/Users/naturist/MusicProject/AI-Project-Incubation-Factory/projects/debt-collection`。

### 步骤 3（终端A）：装测试依赖（只需一次）
```bash
uv pip install -e ".[dev]" -i https://mirrors.aliyun.com/pypi/simple
```
- ✅ 预期：最后一行类似 `Installed N packages`，含 `pytest`。
- ❓ 若 `uv: command not found`：先 `source ~/.venv/bin/activate` 没做对，回步骤1。

### 步骤 4（终端A）：跑测试
```bash
python -m pytest -q
```
- ✅ 预期：`18 passed in ...`（核心模块全过：台账/时效/合规/情报/策略/CLI）。
- ❓ 若有 failed：把完整输出复制存成文件 push 给我（见任务四的 push 方法），我来修。

---

## 任务二：看 GLM 生成的真实策略（对比离线兜底，即 model-ab-test）

> 需要两个终端：终端A 跑 LiteLLM 网关（一直开着），终端B 跑 debt 命令。

### 步骤 1（终端A）：起 LiteLLM 网关（用我们的启动脚本，会自动 export GLM Key）
```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
source ~/.venv/bin/activate
bash _infra/start-litellm.sh
```
- ✅ 预期：看到 `✅ GLM_API_KEY 已加载到环境（长度 39）` 和 `Uvicorn running on ...:4000`。
- ⚠️ **这个终端A 不要关，让它一直跑着**。后续命令都在**新终端B**里执行。
- ❓ 若 `litellm: command not found`：说明 litellm 没装在当前 venv。先 `uv pip install 'litellm[proxy]' -i https://mirrors.aliyun.com/pypi/simple` 再重试。

### 步骤 2（终端B，新开一个终端窗口）：进项目、激活 venv
```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory/projects/debt-collection
source ~/.venv/bin/activate
export PYTHONPATH=src
```
- ✅ 预期：提示符有 venv 前缀。`export PYTHONPATH=src` 让 python 找到 debt 模块。

### 步骤 3（终端B）：录入一笔测试债务 + 加情报
```bash
python -m debt.cli --db runtime/debt.db add "测试债务人" 50000 --due 2025-01-01 --region 浙江杭州 --evidence "借条,转账记录"
python -m debt.cli --db runtime/debt.db intel 1 "债务人当选村支书" --source 朋友
```
- ✅ 预期：分别看到 `✅ 已录入债务 #1` 和 `✅ 已为债务 #1 添加情报 #1`。
- 说明：数据存在 `runtime/debt.db`（已被 .gitignore 忽略，不会入库/外泄）。

### 步骤 4（终端B）：先看离线版（关掉网关感受兜底）→ 再看 GLM 版（开网关）
**先看 GLM 版**（网关在终端A 开着）：
```bash
python -m debt.cli --db runtime/debt.db report 1
```
- ✅ 预期：报告底部显示 `模型：cloud/glm-primary | 合规：✅通过`，正文是 GLM 生成的、更深入的策略。
- ❓ 若显示 `模型：offline-template`：说明没连上网关 → 确认终端A 的网关还开着、端口是 4000；或网关用了别的端口(看终端A 输出的实际端口)。

**对比离线版**（切到本地模型或停网关）：
```bash
# 方式1：指定本地模型（需 ollama 在跑）—— 改 strategy 默认模型需改代码，简单起见用方式2
# 方式2：临时停掉终端A 的网关(Ctrl+C)，再跑一次：
python -m debt.cli --db runtime/debt.db report 1
```
- ✅ 预期：这次显示 `模型：offline-template`，正文是规则兜底版。
- 📌 **这就是 model-ab-test**：对比 GLM 版 vs 离线版的差距，感受"模型能帮上多少忙"。把两份结果对比告诉我，我记入工厂能力评估。

### 清理（可选）
```bash
rm -f runtime/debt.db   # 删掉测试数据
```

---

## 任务三（可选）：安装 browser-act / MediaCrawler

### browser-act（交互式查询，验证码人工协助）
**（终端B 或任意终端）**
```bash
# 它用 uv 的 tool 安装方式（独立，不污染项目 venv）
uv tool install browser-act-cli --python 3.12
browser-act --help
```
- ✅ 预期：`browser-act --help` 打印帮助。
- ⚠️ 隐私提示：它在"验证码协助"时会把**验证码图片**发到 browseract.com 的 API（官方称不传 cookie/页面内容）。介意就别用验证码协助功能、改人工过。

### MediaCrawler（社交平台情报，⚠️ 个人自用研究为限）
**（建议独立目录+独立 venv，避免污染）**
```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
mkdir -p runtime/mediacrawler && cd runtime/mediacrawler
git clone https://github.com/NanmiCoder/MediaCrawler.git .
uv venv --python 3.11 && source .venv/bin/activate
uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
# 具体抓取命令见其 README；首次需扫码登录对应平台
```
- ⚠️ 合规：仅个人研究、看公开内容；不要商用、不要散布他人隐私；社交内容须经我们 sources.yaml 分级+交叉验证后才进情报库。
- ❓ 装在 `runtime/` 下，已被 .gitignore 忽略，不会污染项目/不入库。

---

## 任务四：怎么把结果 push 给我分析（不用手动粘贴）
```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
# 把要给我看的输出存成文件，例如：
python -m debt.cli --db /tmp/x.db report 1 > build-verify-output.txt 2>&1   # 举例
git add build-verify-output.txt
git commit -m "build verify output"
git push
```
- 然后告诉我"push 好了"，我会 git pull 拉取分析。

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-12 02:10:00 | 初版：BUILD 验证 + GLM对比 + browser-act/MediaCrawler 安装 保姆级步骤 | Claude Sonnet 4.5 |
