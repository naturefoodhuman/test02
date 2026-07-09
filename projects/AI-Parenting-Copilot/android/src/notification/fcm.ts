// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

import { ApiClient } from '../api/client';
import { AlertDTO } from '../features/alert_center/viewModel';

export type FcmAlertPayload = {
  alert_id: string;
  level: 'gray' | 'blue' | 'yellow' | 'orange' | 'red';
  type: string;
};

export function parseFcmAlertPayload(payload: Record<string, string>): FcmAlertPayload {
  return { alert_id: payload.alert_id, level: payload.level as FcmAlertPayload['level'], type: payload.type };
}

export async function fetchAlertDetail(api: ApiClient, payload: FcmAlertPayload): Promise<AlertDTO> {
  const response = await fetch(`${api.baseUrl}/api/v1/alerts/${payload.alert_id}`, { headers: api.headers() });
  return response.json();
}
