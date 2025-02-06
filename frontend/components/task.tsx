export interface Task {
  id: string;
  title: string;
  description?: string;
  status: "TODO" | "IN_PROGRESS" | "COMPLETED";
  priority: "LOW" | "MEDIUM" | "HIGH";
  dueDate?: string;
  subtasks: Array<Subtask>;
}

export interface Subtask {
  id: string;
  parentId: string;
  title: string;
  description?: string;
  isDone: boolean;
}
