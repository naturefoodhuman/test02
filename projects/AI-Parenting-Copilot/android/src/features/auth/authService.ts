// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


import { ApiClient } from '../../api/client';
import { SessionState } from '../../state/session';

export type LoginInput = {
  familyId: string;
  displayName: string;
  secret: string;
  deviceId?: string;
};

export type DeviceRegistrationInput = {
  kind: 'phone' | 'camera' | 'mmwave' | 'mac';
  name?: string;
  fcmToken?: string;
};

export async function login(api: ApiClient, input: LoginInput): Promise<SessionState> {
  const response = await api.post<{
    access_token: string;
    family_id: string;
    user_id: string;
    role: SessionState['role'];
    device_id?: string;
  }>('/api/v1/auth/login', {
    family_id: input.familyId,
    display_name: input.displayName,
    secret: input.secret,
    device_id: input.deviceId,
  });
  api.setToken(response.data.access_token);
  return {
    accessToken: response.data.access_token,
    familyId: response.data.family_id,
    userId: response.data.user_id,
    role: response.data.role,
    deviceId: response.data.device_id,
  };
}

export async function registerDevice(api: ApiClient, input: DeviceRegistrationInput): Promise<string> {
  const response = await api.post<{ device_id: string }>('/api/v1/auth/devices/register', {
    kind: input.kind,
    name: input.name,
    fcm_token: input.fcmToken,
  });
  return response.data.device_id;
}
