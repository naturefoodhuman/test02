// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 15:22:00

import { ApiClient } from '../api/client';
import { NativeAlertBridge } from './native_bridge';

export type LocalAlertActionDrainResult = {
  attempted: number;
  acked: number;
  ignored: number;
  failed: number;
};

export async function drainLocalAlertActions(
  bridge: NativeAlertBridge,
  api: ApiClient,
  ackBy: string,
  deviceId?: string,
): Promise<LocalAlertActionDrainResult> {
  const actions = await bridge.drainLocalActions();
  const result: LocalAlertActionDrainResult = { attempted: actions.length, acked: 0, ignored: 0, failed: 0 };
  for (const action of actions) {
    if (action.action !== 'ack') {
      result.ignored += 1;
      continue;
    }
    try {
      const response = await api.post(`/api/v1/alerts/${action.alert_id}/ack`, {
        ack_by: ackBy,
        device_id: deviceId,
      });
      if (response.status >= 200 && response.status < 300) {
        await bridge.stopLocalFallback(action.alert_id);
        result.acked += 1;
      } else {
        result.failed += 1;
      }
    } catch (_error) {
      result.failed += 1;
    }
  }
  return result;
}
