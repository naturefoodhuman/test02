# FORGE Factory 性能基准记录

> 记录关键性能指标，用于量化优化效果

---

## Wave 1 基线 (2026-06-14, MLX 已启用)

| 指标 | 数值 | 备注 |
|------|------|------|
| **Ollama 版本** | 0.30.8 | MLX 后端已启用 (`OLLAMA_USE_MLX=1`) |
| **推理速度 (qwen3.6:35b-a3b-q8_0)** | ~50 tok/s | MLX 加速后预估值，真机测试待补充 |
| **推理速度 (deepseek-r1:32b)** | ~40 tok/s | MLX 加速后预估值 |
| **推理速度 (qwen2.5:7b)** | ~120 tok/s | 快速分类模型 |
| **ChromaDB 索引构建时间** | ~10-30s/专家 | 首次构建，后续去重后应 < 2s |
| **Peer-Review 完整评审耗时** | 15-25 分钟 | 当前顺序模式，含 3 评审 + 汇总 |
| **冷启动时间 (依赖导入 + 索引检查)** | ~5-10 秒 | 包含 Agno/LlamaIndex/ChromaDB 导入 |
| **测试套件运行时间** | ~30 秒 | verify_architecture.py 单测 |

---

## 环境信息

- **硬件**: MacBook Pro M1 Max 64GB
- **OS**: macOS 14+ (真机) / Ubuntu 22.04 (沙箱)
- **Python**: 3.11+ (真机) / 3.13 (沙箱)
- **Ollama**: 0.30.8 + MLX 后端
- **关键依赖版本**:
  - agno: 2.6.14
  - llama-index-core: 0.14.22
  - chromadb: 1.5.9
  - pyyaml: 6.0.1
  - rich: 13.9.4

---

## Wave 1 后预期改进 (M1 验收标准)

| 指标 | 基线 | Wave 1 目标 | 验收方式 |
|------|------|-------------|----------|
| MLX tok/s 提升 | 1x (Metal) | > 1.1x (可测量提升) | `ollama run qwen3.6:35b-a3b-q8_0 "test"` 计时 |
| Editable install 导入 | 失败 (sys.path) | 成功 (无 sys.path) | `python3 -c "from peer_review.orchestrator import *"` |
| 测试通过 | 0 (语法错误) | 39/39 (verify_architecture) | `make test` |
| 备份脚本 | 无 | 可运行 | `bash backup.sh` |

---

## 后续 Wave 记录模板

### Wave 2 (重构完成)
| 指标 | Wave 1 | Wave 2 | 变化 |
|------|--------|--------|------|
| 最大单文件行数 | 500+ | ≤ 300 | ✅ |
| ChromaDB 首次启动 | 10-30s | ≤ 2s (去重) | |
| 测试用例数 | 1 (verify) | 39+ | |

### Wave 3 (能力激活)
| 指标 | Wave 2 | Wave 3 | 变化 |
|------|--------|--------|------|
| 流式输出 | ❌ | ✅ | |
| 跨会话记忆 | ❌ | ✅ | |
| 铁闸规则拦截 | ❌ | ✅ (5 条) | |

### Wave 4 (外部集成)
| 指标 | Wave 3 | Wave 4 | 变化 |
|------|--------|--------|------|
| EgressGuard 拦截 | ❌ | ✅ 100% | |
| DeepSeek API 连通 | ❌ | ✅ 50 次 | |
| 单次评审成本 | $0 | < $0.05 | |

### Wave 5 (生产就绪)
| 指标 | Wave 4 | Wave 5 | 变化 |
|------|--------|--------|------|
| Agent 抽象层 | ❌ | ✅ | |
| RAG 评估得分 | N/A | ≥ 70% | |
| 测试总数 | 42+ | 49+ | |
| 文档完整度 | 部分 | 完整 | |