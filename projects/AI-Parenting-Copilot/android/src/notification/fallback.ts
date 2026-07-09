// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

export type LocalFallbackState = {
  ringing: boolean;
  vibrating: boolean;
  alertId?: string;
};

export function startLocalFallback(alertId: string): LocalFallbackState {
  return { ringing: true, vibrating: true, alertId };
}

export function stopLocalFallback(): LocalFallbackState {
  return { ringing: false, vibrating: false };
}
