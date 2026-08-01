// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 22:45:00

import { ApiClient } from '../../api/client';

export type RuleDomain = 'medication' | 'triage' | 'thresholds' | 'vaccine' | 'growth';

export type RuleResultDTO = {
  domain: string;
  verdict: string;
  outputs: Record<string, unknown>;
  evidence: Array<Record<string, unknown>>;
  rule_version: string;
  reason_code: string;
};

export async function evaluateRuleDomain(
  api: ApiClient,
  domain: RuleDomain,
  payload: Record<string, unknown>,
): Promise<RuleResultDTO> {
  const response = await api.post<{ result: RuleResultDTO }>(`/api/v1/rules/evaluate/${domain}`, {
    payload,
  });
  return response.data.result;
}

export function medicationSafetySummary(result: RuleResultDTO): string {
  const doseMl = result.outputs.dose_ml;
  const level = result.outputs.alert_level;
  if (result.verdict === 'block') {
    return `Blocked: ${result.reason_code}`;
  }
  if (doseMl !== undefined) {
    return `Rule Engine dose_ml=${String(doseMl)} (${result.rule_version})`;
  }
  return `Medication rule result: ${level ?? result.verdict}`;
}

export function triageSummary(result: RuleResultDTO): string {
  return `Triage ${String(result.outputs.alert_level ?? 'none')}: ${result.reason_code}`;
}

export function vaccineSummary(result: RuleResultDTO): string {
  const planned = Array.isArray(result.outputs.planned) ? result.outputs.planned : [];
  return `Vaccine items: ${planned.length}`;
}

export function growthSummary(result: RuleResultDTO): string {
  return `Growth percentile: ${String(result.outputs.percentile_band ?? 'unknown')}`;
}
