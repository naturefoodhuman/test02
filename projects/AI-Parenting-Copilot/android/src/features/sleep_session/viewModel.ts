// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

import { ApiClient } from '../../api/client';

export type SleepSessionState = 'active' | 'paused' | 'ended';

export type ROI = { x: number; y: number; width: number; height: number };

export type SleepSessionViewModel = {
  sessionId?: string;
  state?: SleepSessionState;
  analysisVisible: boolean;
  shadowModeLabel: string;
  roi?: ROI;
};

export function buildSleepSessionViewModel(session?: { id: string; state: SleepSessionState; roi_config?: ROI }): SleepSessionViewModel {
  return {
    sessionId: session?.id,
    state: session?.state,
    analysisVisible: session?.state === 'active',
    shadowModeLabel: '影子模式，不强提醒',
    roi: session?.roi_config,
  };
}

export async function saveROI(api: ApiClient, sessionId: string, roi: ROI): Promise<unknown> {
  const response = await api.post<unknown>(`/api/v1/sleep-sessions/${sessionId}/roi`, roi);
  return response.data;
}
