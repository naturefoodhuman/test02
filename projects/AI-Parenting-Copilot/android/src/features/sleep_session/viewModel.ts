// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-02 02:24:00

import { ApiClient } from '../../api/client';

export type SleepSessionState = 'active' | 'paused' | 'ended';

export type ROI = { x: number; y: number; width: number; height: number };

export type SleepSessionDTO = {
  id: string;
  baby_id: string;
  family_id: string;
  state: SleepSessionState;
  roi_config?: ROI;
};

export type CameraEventDTO = {
  id: string;
  camera_id: string;
  session_id?: string;
  kind: string;
  confidence?: number;
  clip_path?: string;
};

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

export async function startSleepSession(
  api: ApiClient,
  babyId: string,
  familyId: string,
): Promise<SleepSessionDTO> {
  const response = await api.post<SleepSessionDTO>('/api/v1/sleep-sessions', {
    baby_id: babyId,
    family_id: familyId,
  });
  return response.data;
}

export async function pauseSleepSession(api: ApiClient, sessionId: string): Promise<SleepSessionDTO> {
  const response = await api.post<SleepSessionDTO>(`/api/v1/sleep-sessions/${sessionId}/pause`, {});
  return response.data;
}

export async function resumeSleepSession(api: ApiClient, sessionId: string): Promise<SleepSessionDTO> {
  const response = await api.post<SleepSessionDTO>(`/api/v1/sleep-sessions/${sessionId}/resume`, {});
  return response.data;
}

export async function endSleepSession(api: ApiClient, sessionId: string): Promise<SleepSessionDTO> {
  const response = await api.post<SleepSessionDTO>(`/api/v1/sleep-sessions/${sessionId}/end`, {});
  return response.data;
}

export async function saveROI(api: ApiClient, sessionId: string, roi: ROI): Promise<SleepSessionDTO> {
  const response = await api.put<SleepSessionDTO>(`/api/v1/sleep-sessions/${sessionId}/roi`, roi);
  return response.data;
}

export async function fetchCameraEvents(api: ApiClient, sessionId: string): Promise<CameraEventDTO[]> {
  const response = await api.get<CameraEventDTO[]>(`/api/v1/sleep-sessions/${sessionId}/camera-events`);
  return response.data;
}
