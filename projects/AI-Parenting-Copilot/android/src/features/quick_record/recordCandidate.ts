// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


export type RecordCandidate = {
  eventType: 'feeding' | 'diaper' | 'temperature' | 'sleep' | 'unknown';
  payload: Record<string, unknown>;
  confidence: number;
  requiresConfirmation: boolean;
};

const feedingPattern = /(喂|喝|奶).*?(\d+(?:\.\d+)?)\s*(ml|毫升)/i;
const temperaturePattern = /(\d{2}(?:\.\d)?)\s*(度|℃|c)/i;

export function buildRecordCandidate(text: string): RecordCandidate {
  const feeding = feedingPattern.exec(text);
  if (feeding) {
    return {
      eventType: 'feeding',
      payload: { amount_ml: Number(feeding[2]) },
      confidence: 0.92,
      requiresConfirmation: true,
    };
  }
  const temperature = temperaturePattern.exec(text);
  if (temperature) {
    return {
      eventType: 'temperature',
      payload: { value_c: Number(temperature[1]) },
      confidence: 0.88,
      requiresConfirmation: true,
    };
  }
  if (/尿布|纸尿裤|便便|大便|尿/.test(text)) {
    return { eventType: 'diaper', payload: { note: text }, confidence: 0.75, requiresConfirmation: true };
  }
  return { eventType: 'unknown', payload: { raw_text: text }, confidence: 0.2, requiresConfirmation: true };
}
