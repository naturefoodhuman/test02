// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 21:12:00

import { ApiClient } from '../api/client';
import { LocalObservationEvent } from './schema';
import { NativeLocalEventBridge } from './native_sqlite_bridge';

export type PendingSyncDrainResult = {
  attempted: number;
  synced: number;
  failed: number;
  failedEventIds: string[];
};

export function toServerObservationEvent(event: LocalObservationEvent): Omit<LocalObservationEvent, 'pending_sync'> & {
  correction_of?: string | null;
  is_deleted?: boolean;
} {
  const { pending_sync: _pendingSync, ...payload } = event;
  return { ...payload, correction_of: null, is_deleted: false };
}

export async function reportSyncHeartbeat(
  api: ApiClient,
  clientId: string,
  familyId: string | undefined,
  pendingCount: number,
): Promise<void> {
  await api.post('/api/v1/sync/heartbeat', {
    client_id: clientId,
    family_id: familyId,
    pending_count: pendingCount,
  });
}

export async function drainPendingEvents(
  bridge: NativeLocalEventBridge,
  api: ApiClient,
  clientId?: string,
  familyId?: string,
): Promise<PendingSyncDrainResult> {
  const pending = await bridge.pending();
  const result: PendingSyncDrainResult = { attempted: pending.length, synced: 0, failed: 0, failedEventIds: [] };
  for (const event of pending) {
    try {
      const response = await api.post('/api/v1/events', toServerObservationEvent(event));
      if (response.status >= 200 && response.status < 300) {
        await bridge.markSynced(event.event_id);
        result.synced += 1;
      } else {
        result.failed += 1;
        result.failedEventIds.push(event.event_id);
      }
    } catch (_error) {
      result.failed += 1;
      result.failedEventIds.push(event.event_id);
    }
  }
  if (clientId) {
    await reportSyncHeartbeat(api, clientId, familyId, result.failed);
  }
  return result;
}
