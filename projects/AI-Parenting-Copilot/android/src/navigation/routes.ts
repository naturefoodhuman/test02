// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


export const routes = {
  Auth: 'Auth',
  Today: 'Today',
  QuickRecord: 'QuickRecord',
  Timeline: 'Timeline',
  AlertCenter: 'AlertCenter',
  SleepSession: 'SleepSession',
} as const;

export type RouteName = keyof typeof routes;

export const defaultRouteOrder: RouteName[] = [
  'Today',
  'QuickRecord',
  'Timeline',
  'AlertCenter',
  'SleepSession',
];
