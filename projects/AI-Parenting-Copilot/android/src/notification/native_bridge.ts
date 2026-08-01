// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 03:02:00

import { FcmAlertPayload } from './fcm';

export type NativeAlertBridge = {
  showCriticalAlert(payload: FcmAlertPayload): Promise<void>;
  stopLocalFallback(alertId: string): Promise<void>;
  drainLocalActions(): Promise<Array<{ alert_id: string; action: 'ack' | 'dismiss_local' | 'unknown' }>>;
};

export function shouldUseFullScreen(level: FcmAlertPayload['level']): boolean {
  return level === 'red' || level === 'orange';
}

export async function handleNativeAlert(
  bridge: NativeAlertBridge,
  payload: FcmAlertPayload,
): Promise<'fullscreen' | 'silent'> {
  if (shouldUseFullScreen(payload.level)) {
    await bridge.showCriticalAlert(payload);
    return 'fullscreen';
  }
  return 'silent';
}
