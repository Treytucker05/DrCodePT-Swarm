
export enum Priority {
  High = 'High',
  Medium = 'Medium',
  Low = 'Low'
}

export interface Subtask {
  id: string;
  title: string;
  isCompleted: boolean;
  subtasks: Subtask[];
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  dueDate?: string; // ISO String
  priority: Priority;
  category: string;
  subtasks: Subtask[];
  isCompleted: boolean;
  createdAt: string;
  order: number;
}

export interface AISubtask {
  id?: string;
  title: string;
  subtasks?: AISubtask[];
}

export interface AIParseResult {
  tasks: Array<{
    id?: string; // AI might return an existing ID or "NEW"
    title: string;
    description?: string;
    dueDate?: string;
    priority: string;
    category: string;
    subtasks?: AISubtask[];
  }>;
}
