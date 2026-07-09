// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


export type PowerSyncConfig = {
  endpoint: string;
  enabled: boolean;
};

export function createPowerSyncConfig(endpoint = 'http://127.0.0.1:8080'): PowerSyncConfig {
  return { endpoint, enabled: true };
}
