// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

export type FullScreenIntentGuide = {
  requiresPermission: boolean;
  permissionName: string;
  batteryWhitelistRecommended: boolean;
};

export function buildFullScreenIntentGuide(androidApiLevel: number): FullScreenIntentGuide {
  return {
    requiresPermission: androidApiLevel >= 34,
    permissionName: 'USE_FULL_SCREEN_INTENT',
    batteryWhitelistRecommended: true,
  };
}
