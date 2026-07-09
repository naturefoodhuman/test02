// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

export type NotificationChannelConfig = {
  id: string;
  name: string;
  importance: 'default' | 'high';
  fullScreen: boolean;
  vibration: boolean;
  sound: boolean;
};

export function channelForLevel(level: string): NotificationChannelConfig {
  const high = level === 'red' || level === 'orange';
  return {
    id: high ? 'parenting-critical-alerts' : 'parenting-alerts',
    name: high ? 'Parenting Critical Alerts' : 'Parenting Alerts',
    importance: high ? 'high' : 'default',
    fullScreen: high,
    vibration: high,
    sound: high,
  };
}
