// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


export type EventSource = 'manual' | 'voice_text' | 'camera' | 'sensor' | 'ai' | 'system';

export type LocalObservationEvent = {
  event_id: string;
  baby_id: string;
  family_id: string;
  user_id?: string;
  device_id?: string;
  event_type: string;
  client_created_at: string;
  start_time: string;
  payload: Record<string, unknown>;
  source: EventSource;
  confidence: number;
  pending_sync: boolean;
};

export const observationEventColumns = [
  'event_id',
  'baby_id',
  'family_id',
  'user_id',
  'device_id',
  'event_type',
  'client_created_at',
  'start_time',
  'payload',
  'source',
  'confidence',
  'pending_sync',
] as const;
