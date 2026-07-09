// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


import { LocalObservationEvent } from './schema';

export class InMemoryLocalEventStore {
  private events: LocalObservationEvent[] = [];

  insert(event: Omit<LocalObservationEvent, 'pending_sync'>): LocalObservationEvent {
    const stored = { ...event, pending_sync: true };
    this.events.push(stored);
    return stored;
  }

  pending(): LocalObservationEvent[] {
    return this.events.filter((event) => event.pending_sync);
  }

  all(): LocalObservationEvent[] {
    return [...this.events];
  }
}
