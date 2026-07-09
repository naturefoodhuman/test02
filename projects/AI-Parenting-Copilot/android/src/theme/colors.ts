// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


export const colors = {
  light: {
    background: '#FFFFFF',
    foreground: '#1F2937',
    primary: '#2563EB',
    danger: '#DC2626',
  },
  dark: {
    background: '#0F172A',
    foreground: '#E5E7EB',
    primary: '#60A5FA',
    danger: '#F87171',
  },
} as const;

export type ThemeMode = keyof typeof colors;
