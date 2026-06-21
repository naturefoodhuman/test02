# config_loader

网络配置加载模块（增量）。

**职责**：
- 严格加载 `config/network.yaml`
- 使用 Pydantic 校验（与现有 FORGE schemas 风格一致）
- 提供 `load_network_config()` 供所有模块使用

**复用模式**：
直接复用 `peer_review.config.loader` + `schemas` 的设计哲学。

后续模块应优先使用：
```python
from _infra.network.config_loader import load_network_config
cfg = load_network_config()
print(cfg.search.searxng.base_url)
```
