// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-02 16:16:00

import { ApiClient, defaultApiClient } from '../../api/client';
import { LocalObservationEvent } from '../../sync/schema';
import { createLocalEventFromCandidate, LocalEventContext } from './createLocalEvent';
import { buildRecordCandidate, RecordCandidate } from './recordCandidate';

export type CopilotRecordCandidateContext = {
  babyId: string;
  familyId: string;
  userId?: string;
  deviceId?: string;
};

export type CopilotQueryResponse = {
  intent: string;
  copilot_response?: {
    payload?: {
      record_candidate?: {
        event_type?: string;
        normalized_payload?: Record<string, unknown>;
        confidence?: number;
      };
    };
    requires_confirmation?: boolean;
  };
};

export type ConfirmRecordCandidateResponse = {
  event_id: string;
  event_type: string;
  payload: Record<string, unknown>;
};

const supportedEventTypes = ['feeding', 'diaper', 'temperature', 'sleep', 'unknown'] as const;

type SupportedEventType = (typeof supportedEventTypes)[number];

function supportedEventType(value: string | undefined): SupportedEventType {
  if (supportedEventTypes.includes(value as SupportedEventType)) {
    return value as SupportedEventType;
  }
  return 'unknown';
}

export function mapServerRecordCandidate(response: CopilotQueryResponse, fallbackText: string): RecordCandidate {
  const candidate = response.copilot_response?.payload?.record_candidate;
  if (!candidate) {
    return buildRecordCandidate(fallbackText);
  }
  return {
    eventType: supportedEventType(candidate.event_type),
    payload: candidate.normalized_payload ?? { raw_text: fallbackText },
    confidence: candidate.confidence ?? 0.2,
    requiresConfirmation: true,
  };
}

export async function fetchCopilotRecordCandidate(
  text: string,
  context: CopilotRecordCandidateContext,
  client: ApiClient = defaultApiClient,
): Promise<RecordCandidate> {
  const response = await client.post<CopilotQueryResponse>('/api/v1/copilot/query', {
    text,
    baby_id: context.babyId,
    family_id: context.familyId,
    intent: 'record',
    context: {},
  });
  if (response.status < 200 || response.status >= 300) {
    return buildRecordCandidate(text);
  }
  return mapServerRecordCandidate(response.data, text);
}

export async function confirmCopilotRecordCandidate(
  candidate: RecordCandidate,
  context: CopilotRecordCandidateContext,
  rawText: string,
  client: ApiClient = defaultApiClient,
): Promise<ConfirmRecordCandidateResponse> {
  const response = await client.post<ConfirmRecordCandidateResponse>(
    '/api/v1/copilot/record-candidates/confirm',
    {
      baby_id: context.babyId,
      family_id: context.familyId,
      user_id: context.userId,
      device_id: context.deviceId,
      event_type: candidate.eventType,
      normalized_payload: candidate.payload,
      confidence: candidate.confidence,
      raw_text: rawText,
      source: 'manual',
    },
  );
  return response.data;
}

export async function createLocalEventFromCopilotText(
  text: string,
  context: CopilotRecordCandidateContext & LocalEventContext,
  client: ApiClient = defaultApiClient,
): Promise<Omit<LocalObservationEvent, 'pending_sync'>> {
  const candidate = await fetchCopilotRecordCandidate(text, context, client);
  return createLocalEventFromCandidate(candidate, context);
}
