import { Task, Run, RunDetails, HandoffState } from '../types';

const json = async <T>(url: string, options?: RequestInit): Promise<T> => {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
};

export const api = {
  getTasks: async (): Promise<Task[]> => {
    return json<Task[]>('/api/tasks');
  },

  runTask: async (taskName: string): Promise<{ success: boolean; runId: string }> => {
    return json<{ success: boolean; runId: string }>('/api/run', {
      method: 'POST',
      body: JSON.stringify({ task: taskName }),
    });
  },

  getRuns: async (): Promise<Run[]> => {
    return json<Run[]>('/api/runs');
  },

  getRunDetails: async (id: string): Promise<RunDetails> => {
    return json<RunDetails>(`/api/runs/${id}`);
  },

  getEnvKeys: async (): Promise<string[]> => {
    return json<string[]>('/api/env/keys');
  },

  setEnv: async (key: string, value: string): Promise<void> => {
    await json('/api/env', {
      method: 'POST',
      body: JSON.stringify({ key, value }),
    });
  },

  getHandoffState: async (): Promise<HandoffState> => {
    return json<HandoffState>('/api/handoff');
  },

  createContinueFlag: async (): Promise<void> => {
    await json('/api/handoff/continue', { method: 'POST' });
  },

  sendChatMessage: async (message: string): Promise<string> => {
    const resp = await json<{ reply: string }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    return resp.reply;
  },
};
