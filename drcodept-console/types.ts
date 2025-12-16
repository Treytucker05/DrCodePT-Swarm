export type TaskType = 'browser' | 'shell' | 'api' | 'python' | 'fs' | 'composite';

export interface Task {
  name: string;
  type: TaskType;
  goal: string;
  yamlContent: string; // Mocked for the modal
}

export type RunStatus = 'success' | 'failed' | 'escalated' | 'in-progress';

export interface Run {
  id: string;
  task: string;
  status: RunStatus;
  startedAt: string;
  duration: string;
}

export interface Evidence {
  name: string;
  url: string;
  type: 'image' | 'file' | 'html';
  size?: string;
}

export interface RunDetails extends Run {
  summary: string;
  evidence: Evidence[];
  events: LogEvent[];
  isWaiting?: boolean; // If blocked on handoff
}

export interface LogEvent {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
}

export interface HandoffState {
  waiting: boolean;
  content?: string;
  continuePresent: boolean;
}

export interface EnvKey {
  name: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: Date;
}