import React, { useState, useEffect } from "react";
import { Task } from "./tasksTypes";

interface TaskFormProps {
  task?: Task;
  parentTaskId?: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskData: TaskFormData) => Promise<void>;
}

export interface TaskFormData {
  title: string;
  task_type: "Meeting" | "Training" | "Studies";
  description: string;
  status: "TODO" | "IN_PROGRESS" | "COMPLETED";
  priority: "LOW" | "MEDIUM" | "HIGH";
  dueDate?: string;
  durationMinutes: number;
}

const TaskForm: React.FC<TaskFormProps> = ({
  task,
  parentTaskId,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const defaultData: TaskFormData = {
    title: "",
    task_type: "Meeting",
    description: "",
    status: "TODO",
    priority: "MEDIUM",
    dueDate: undefined,
    durationMinutes: 60,
  };
  const [formData, setFormData] = useState<TaskFormData>(defaultData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title,
        task_type: task.task_type,
        description: task.description || "",
        status: task.status,
        priority: task.priority,
        dueDate: task.dueDate,
        durationMinutes: task.durationMinutes || 60,
      });
    }
  }, [task, parentTaskId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await onSubmit(formData);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save task");
    } finally {
      setLoading(false);
      setFormData(defaultData);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black backdrop:opacity-50 flex items-center justify-center z-50">
      <div className="bg-base-100 backdrop:opacity-50 rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="p-6">
          <div className="flex justify-between  mb-6">
            <h2 className="text-xl font-bold">
              {task ? "Edit Task" : "Create New Task"}
            </h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 opacity-100">
            {error && (
              <div className="alert alert-error">
                <span>{error}</span>
              </div>
            )}

            <div className="form-control">
              <label className="label">
                <span className="label-text">Title*</span>
              </label>
              <input
                type="text"
                placeholder="Enter task title"
                className="input input-bordered w-full"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                required
                data-testid="task-title-input"
              />
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text">Task Type</span>
              </label>
              <select
                className="select select-bordered w-full"
                value={formData.task_type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    task_type: e.target.value as TaskFormData["task_type"],
                  })
                }
                data-testid="task-type-select"
              >
                <option value="Meeting">Meeting</option>
                <option value="Training">Training</option>
                <option value="Studies">Studies</option>
              </select>
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text">Description</span>
              </label>
              <textarea
                placeholder="Enter task description"
                className="textarea textarea-bordered h-24 w-full"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                data-testid="task-description-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Status</span>
                </label>
                <select
                  className="select select-bordered w-full"
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      status: e.target.value as TaskFormData["status"],
                    })
                  }
                  data-testid="task-status-select"
                >
                  <option value="TODO">Todo</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Priority</span>
                </label>
                <select
                  className="select select-bordered w-full"
                  value={formData.priority}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      priority: e.target.value as TaskFormData["priority"],
                    })
                  }
                  data-testid="task-priority-select"
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                </select>
              </div>
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text">Due Date</span>
              </label>
              <input
                type="datetime-local"
                className="input input-bordered w-full"
                name="dueDate"
                value={formData.dueDate || undefined}
                onChange={(e) =>
                  setFormData({ ...formData, dueDate: e.target.value })
                }
                data-testid="task-datetime-input"
              />
            </div>
            <div className="form-control">
              <label className="label">
                <span className="label-text">Duration (minutes)*</span>
              </label>
              <input
                type="number"
                min={1}
                className="input input-bordered w-full"
                value={formData.durationMinutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    durationMinutes: Number(e.target.value),
                  })
                }
                required
              />
              </div>
            <div className="modal-action">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className={`btn btn-primary ${loading ? "loading" : ""}`}
                disabled={loading}
                data-testid="save-task-button"
              >
                {loading ? "Saving..." : "Save Task"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TaskForm;
