# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-19 18:45:00

import json
from pathlib import Path

class StateRegistry:
    """项目状态注册表：防止关机失忆 (需求 7)"""
    
    def __init__(self, state_file: str = "runtime/factory_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self.state_file.write_text("{}")
            
    def save_state(self, project_name: str, thread_id: str, last_action: str):
        data = json.loads(self.state_file.read_text())
        data[project_name] = {
            "thread_id": thread_id,
            "last_action": last_action,
            "timestamp": time.time() if "time" in globals() else 0
        }
        self.state_file.write_text(json.dumps(data, indent=2))
        
    def get_state(self, project_name: str):
        data = json.loads(self.state_file.read_text())
        return data.get(project_name)

# ... 辅助代码 ...
