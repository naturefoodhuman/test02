// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-02 05:20:00

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

export type CameraShadowSummaryDTO = {
  session_id: string;
  event_count: number;
  shadow_count: number;
  kind_counts: Record<string, number>;
  clip_paths: string[];
};

export type CameraShadowEvaluateDTO = {
  decision: Record<string, unknown>;
  clip_plan?: Record<string, unknown>;
  camera_event?: CameraEventDTO;
  vlm?: Record<string, unknown>;
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


export async function fetchCameraShadowSummary(
  api: ApiClient,
  sessionId: string,
): Promise<CameraShadowSummaryDTO> {
  const response = await api.get<CameraShadowSummaryDTO>(`/api/v1/sleep-sessions/${sessionId}/shadow-summary`);
  return response.data;
}

export async function evaluateCameraShadow(
  api: ApiClient,
  payload: {
    camera_id: string;
    session_id: string;
    sleep_session_active: boolean;
    camera_kind?: string;
    camera_confidence?: number;
    mmwave_abnormal_event?: string;
    image_base64?: string;
    dispatch_vlm?: boolean;
  },
): Promise<CameraShadowEvaluateDTO> {
  const response = await api.post<CameraShadowEvaluateDTO>('/api/v1/camera-shadow/evaluate', payload);
  return response.data;
}
