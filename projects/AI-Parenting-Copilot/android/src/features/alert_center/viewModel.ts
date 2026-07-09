// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

import { ApiClient } from '../../api/client';

export type AlertLevel = 'gray' | 'blue' | 'yellow' | 'orange' | 'red';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed';
export type FeedbackType = 'useful' | 'false_positive' | 'too_sensitive' | 'already_known' | 'ignored';

export type AlertDTO = {
  id: string;
  level: AlertLevel;
  type: string;
  status: AlertStatus;
  evidence: Record<string, unknown>;
  recommended_action?: string;
  ack_by?: string;
  ack_at?: string;
};

export type AlertViewModel = {
  id: string;
  title: string;
  level: AlertLevel;
  evidenceRows: string[];
  canAck: boolean;
};

export function buildAlertViewModel(alert: AlertDTO): AlertViewModel {
  return {
    id: alert.id,
    title: `${alert.level.toUpperCase()} · ${alert.type}`,
    level: alert.level,
    evidenceRows: Object.entries(alert.evidence).map(([key, value]) => `${key}: ${String(value)}`),
    canAck: alert.status === 'active',
  };
}

export async function ackAlert(api: ApiClient, alertId: string, ackBy: string, deviceId?: string): Promise<AlertDTO> {
  const response = await api.post<AlertDTO>(`/api/v1/alerts/${alertId}/ack`, {
    ack_by: ackBy,
    device_id: deviceId,
  });
  return response.data;
}

export async function submitFeedback(
  api: ApiClient,
  alertId: string,
  feedback: FeedbackType,
  note?: string,
): Promise<AlertDTO> {
  const response = await api.post<AlertDTO>(`/api/v1/alerts/${alertId}/feedback`, { feedback, note });
  return response.data;
}
