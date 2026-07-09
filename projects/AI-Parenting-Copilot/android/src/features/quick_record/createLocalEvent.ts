// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


import { LocalObservationEvent } from '../../sync/schema';
import { RecordCandidate } from './recordCandidate';

export type LocalEventContext = {
  eventId: string;
  babyId: string;
  familyId: string;
  userId?: string;
  deviceId?: string;
  nowIso: string;
};

export function createLocalEventFromCandidate(
  candidate: RecordCandidate,
  context: LocalEventContext,
): Omit<LocalObservationEvent, 'pending_sync'> {
  return {
    event_id: context.eventId,
    baby_id: context.babyId,
    family_id: context.familyId,
    user_id: context.userId,
    device_id: context.deviceId,
    event_type: candidate.eventType,
    client_created_at: context.nowIso,
    start_time: context.nowIso,
    payload: candidate.payload,
    source: 'manual',
    confidence: candidate.confidence,
  };
}
