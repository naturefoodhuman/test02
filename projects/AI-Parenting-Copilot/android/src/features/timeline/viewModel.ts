// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

import { LocalObservationEvent } from '../../sync/schema';

export type TimelineItem = LocalObservationEvent & {
  day: string;
  displaySource: string;
  duplicateHint?: string;
};

export type CorrectionPayload = {
  correction_of: string;
  normalized_payload: Record<string, unknown>;
  reason?: string;
};

export function buildTimelineItems(events: LocalObservationEvent[]): TimelineItem[] {
  const sorted = [...events].sort((a, b) => b.start_time.localeCompare(a.start_time));
  return sorted.map((event, index) => ({
    ...event,
    day: event.start_time.slice(0, 10),
    displaySource: `${event.user_id ?? 'unknown'} / ${event.source}`,
    duplicateHint: duplicateFeedingHint(event, sorted[index + 1]),
  }));
}

export function duplicateFeedingHint(
  event: LocalObservationEvent,
  previous?: LocalObservationEvent,
): string | undefined {
  if (!previous || event.event_type !== 'feeding' || previous.event_type !== 'feeding') {
    return undefined;
  }
  const deltaMs = Math.abs(Date.parse(event.start_time) - Date.parse(previous.start_time));
  return deltaMs <= 5 * 60 * 1000 ? '5分钟内存在疑似重复喂奶记录，请人工确认。' : undefined;
}

export function createCorrectionPayload(
  event: LocalObservationEvent,
  normalizedPayload: Record<string, unknown>,
  reason?: string,
): CorrectionPayload {
  return { correction_of: event.event_id, normalized_payload: normalizedPayload, reason };
}

export function createSoftDeletePayload(event: LocalObservationEvent): { event_id: string; is_deleted: true } {
  return { event_id: event.event_id, is_deleted: true };
}
