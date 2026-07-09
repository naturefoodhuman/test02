// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

export type WorkRequest = {
  name: string;
  constraints: string[];
  reason: string;
};

export function buildBackgroundSyncWork(): WorkRequest {
  return {
    name: 'parenting-background-sync',
    constraints: ['network_connected', 'battery_not_low'],
    reason: 'flush pending_sync local observation events',
  };
}
