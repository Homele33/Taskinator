export interface Task {
  id: string;
  title: string;
  task_type: "Meeting" | "Training" | "Studies";
  description?: string;
  status: "TODO" | "IN_PROGRESS" | "COMPLETED";
  priority: "LOW" | "MEDIUM" | "HIGH";
  dueDate?: string;
  subtasks: Array<Subtask>;
  durationMinutes: number; 
  scheduledStart?: string | null; 
  scheduledEnd?: string | null;
}

export interface Subtask {
  id: string;
  parentId: string;
  title: string;
  description?: string;
  isDone: boolean;
}
