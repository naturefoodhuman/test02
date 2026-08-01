// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 04:46:00

import { SessionState } from '../../state/session';

export type NativeSecureSessionBridge = {
  save(session: Required<Pick<SessionState, 'accessToken' | 'familyId' | 'userId'>> & Partial<SessionState>): Promise<void>;
  load(): Promise<SessionState | undefined>;
  clear(): Promise<void>;
};

export async function persistSession(
  bridge: NativeSecureSessionBridge,
  session: Required<Pick<SessionState, 'accessToken' | 'familyId' | 'userId'>> & Partial<SessionState>,
): Promise<SessionState> {
  await bridge.save(session);
  return session;
}

export async function restoreSession(bridge: NativeSecureSessionBridge): Promise<SessionState | undefined> {
  return bridge.load();
}

export async function clearSession(bridge: NativeSecureSessionBridge): Promise<void> {
  await bridge.clear();
}
