// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 04:37:00

import { LocalObservationEvent } from './schema';

export type NativeLocalEventBridge = {
  insertPending(event: LocalObservationEvent): Promise<LocalObservationEvent>;
  pending(): Promise<LocalObservationEvent[]>;
  markSynced(eventId: string): Promise<void>;
};

export async function insertPendingLocalEvent(
  bridge: NativeLocalEventBridge,
  event: LocalObservationEvent,
): Promise<LocalObservationEvent> {
  return bridge.insertPending({ ...event, pending_sync: true });
}

export async function markSyncedAfterPowerSync(
  bridge: NativeLocalEventBridge,
  eventId: string,
): Promise<void> {
  await bridge.markSynced(eventId);
}

export async function pendingSyncCount(bridge: NativeLocalEventBridge): Promise<number> {
  return (await bridge.pending()).length;
}
