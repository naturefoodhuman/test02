// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


export type SessionState = {
  accessToken?: string;
  familyId?: string;
  userId?: string;
  babyId?: string;
  deviceId?: string;
  role?: 'Admin' | 'Caregiver' | 'Viewer' | 'System';
};

export type SessionAction =
  | { type: 'login'; payload: Required<Pick<SessionState, 'accessToken' | 'familyId' | 'userId' | 'role'>> & Partial<SessionState> }
  | { type: 'setBaby'; babyId: string }
  | { type: 'logout' };

export function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case 'login':
      return { ...state, ...action.payload };
    case 'setBaby':
      return { ...state, babyId: action.babyId };
    case 'logout':
      return {};
  }
}
