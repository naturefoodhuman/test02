// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 12:00:00

import { LocalObservationEvent } from '../../sync/schema';

export type DerivedBabyState = {
  last_feeding_at?: string;
  feeding_24h_ml?: number;
  diaper_wet_24h?: number;
  sleep_minutes_24h?: number;
  active_alert_count?: number;
};

export type DeviceHealthSnapshot = Record<string, 'online' | 'offline' | 'unknown'>;

export type TodayViewModel = {
  lastFeedingText: string;
  feeding24hText: string;
  diaperText: string;
  sleepText: string;
  pendingSyncCount: number;
  grayDeviceCount: number;
  activeAlertCount: number;
  empty: boolean;
};

export function buildTodayViewModel(
  state: DerivedBabyState | undefined,
  localEvents: LocalObservationEvent[],
  deviceHealth: DeviceHealthSnapshot,
): TodayViewModel {
  const pendingSyncCount = localEvents.filter((event) => event.pending_sync).length;
  const grayDeviceCount = Object.values(deviceHealth).filter((status) => status === 'offline').length;
  return {
    lastFeedingText: state?.last_feeding_at ? `上次喂奶 ${state.last_feeding_at}` : '暂无喂奶记录',
    feeding24hText: `${state?.feeding_24h_ml ?? 0} ml / 24h`,
    diaperText: `${state?.diaper_wet_24h ?? 0} 次湿尿布 / 24h`,
    sleepText: `${state?.sleep_minutes_24h ?? 0} 分钟睡眠 / 24h`,
    pendingSyncCount,
    grayDeviceCount,
    activeAlertCount: state?.active_alert_count ?? 0,
    empty: !state && localEvents.length === 0,
  };
}
