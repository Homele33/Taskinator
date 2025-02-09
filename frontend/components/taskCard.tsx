import React, { useState, useEffect } from "react";
import { Subtask, Task } from "./task";
import SubtaskForm, { SubtaskFormData } from "./subtaskForm";
import { SubtaskCard } from "./subtaskCard";
import { Pencil, Trash2, SquarePlus, Menu, Bot } from "lucide-react";

interface TaskCardProps {
  task: Task;
  level?: number;
  onRefresh: () => void;
  onEdit: (task: Task) => void;
}

const getCardStyles = (level: number) => {
  // Base styles for all cards
  const baseStyles = "card shadow-lg hover:shadow-xl transition-shadow";

  return `${baseStyles} border border-base-200`;
};

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  level = 0,
  onRefresh,
  onEdit,
}) => {
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoadingSubtasks, setIsLoadingSubtasks] = useState(false);
  const [editSubtask, setEditingSubtask] = useState<string | undefined>(
    undefined
  );
  const [isFormOpen, setIsFormOpen] = useState(false);

  useEffect(() => {
    onRefresh;
  }, [subtasks]);

  const fetchSubtasks = async () => {
    setIsLoadingSubtasks(true);
    try {
      const response = await fetch(
        `http://localhost:5000/api/tasks/subtasks/${task.id}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch subtasks");
      }
      const data = await response.json();
      setSubtasks(data);
    } catch (err) {
      console.error("Error fetching subtasks:", err);
    } finally {
      setIsLoadingSubtasks(false);
    }
  };

  const getPriorityColor = (priority: Task["priority"]) => {
    switch (priority) {
      case "HIGH":
        return "badge-error";
      case "MEDIUM":
        return "badge-warning";
      case "LOW":
        return "badge-info";
      default:
        return "badge-ghost";
    }
  };

  const getStatusColor = (status: Task["status"]) => {
    switch (status) {
      case "TODO":
        return "bg-base-200";
      case "IN_PROGRESS":
        return "bg-blue-950";
      case "COMPLETED":
        return "bg-emerald-950";
      default:
        return "bg-base-200";
    }
  };

  const handleAddSubtask = async (subtask: SubtaskFormData) => {
    const response = await fetch(
      `http://localhost:5000/api/tasks/subtasks/${subtask.parentId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(subtask),
      }
    );
    if (!response.ok) {
      throw new Error("Failed to create subtask");
    }
    fetchSubtasks();

    setIsExpanded(true);
  };

  const handleDeleteTask = async (id: string) => {
    const response = await fetch(`http://localhost:5000/api/tasks/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error("Failed to delete task");
    }
    onRefresh();
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    const response = await fetch(
      `http://localhost:5000/api/tasks/status/${id}?status=${newStatus}`,
      {
        method: "PATCH",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to change status");
    }
    onRefresh();
  };

  const handleTaskBreaker = async (id: string) => {
    const response = await fetch(
      `http://localhost:5000/api/task-breaker/${id}`,
      {
        method: "GET",
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to break task`);
    }
  };

  return (
    <div className={`ml-${level * 12}`}>
      <div className={`${getCardStyles(level)} ${getStatusColor(task.status)}`}>
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              {task.subtasks.length === 0 ? (
                <div />
              ) : (
                <button
                  onClick={() => {
                    fetchSubtasks();
                    setIsExpanded(!isExpanded);
                  }}
                  className="btn btn-ghost btn-sm btn-circle"
                >
                  {isLoadingSubtasks ? (
                    <span className="loading loading-spinner loading-xs"></span>
                  ) : (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className={`h-4 w-4 transition-transform ${
                        isExpanded ? "rotate-90" : ""
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  )}
                </button>
              )}
              <h2
                className={`${level > 0 ? "text-lg" : "text-xl"} font-bold  `}
              >
                {task.title}
              </h2>
            </div>
            <div className="flex gap-2">
              <span className={`badge ${getPriorityColor(task.priority)}`}>
                {task.priority}
              </span>
              <div className="dropdown-end dropdown">
                <div>
                  <label
                    tabIndex={0}
                    className="btn btn-ghost btn-circle btn-sm "
                  >
                    <Menu />
                  </label>
                </div>

                <ul
                  tabIndex={0}
                  className="dropdown-content menu p-2 shadow bg-base-100 rounded-box z-20"
                >
                  <div className="tooltip" data-tip="Break task down">
                    <li>
                      <button
                        onClick={() => {
                          handleTaskBreaker(task.id);
                        }}
                        className="btn btn-ghost btn-md text-purple-600"
                      >
                        <Bot /> {/* Task beaker*/}
                      </button>
                    </li>
                  </div>
                  <div className="tooltip" data-tip="add subtask">
                    <li>
                      <button
                        onClick={() => {
                          setIsFormOpen(true);
                          setEditingSubtask(undefined);
                        }}
                        className="btn btn-ghost btn-md text-green-500"
                      >
                        <SquarePlus className="" /> {/* Add subtask icon */}
                      </button>
                    </li>
                  </div>
                  <div className="tooltip" data-tip="Edit task">
                    <li>
                      <button
                        onClick={() => onEdit(task)}
                        className="btn btn-ghost btn-md text-yellow-400"
                      >
                        <Pencil /> {/* Edit icon */}
                      </button>
                    </li>
                  </div>
                  <div className="tooltip" data-tip="Delete">
                    <li>
                      <button
                        onClick={() => handleDeleteTask(task.id)}
                        className="btn btn-ghost btn-md text-error"
                      >
                        <Trash2 /> {/* Delete icon*/}
                      </button>
                    </li>
                  </div>
                </ul>
                <SubtaskForm
                  subtask={undefined}
                  parentId={task.id}
                  isOpen={isFormOpen}
                  onClose={() => {
                    setIsFormOpen(false);
                    setEditingSubtask(undefined);
                  }}
                  onSubmit={handleAddSubtask}
                />
              </div>
            </div>
          </div>

          <p className="text-gray-600">{task.description}</p>

          <div className="flex justify-between items-center mt-4">
            <div className="flex items-center gap-2">
              <select
                className="select select-bordered select-sm"
                value={task.status}
                onChange={(e) => handleStatusChange(task.id, e.target.value)}
              >
                <option value="TODO">Todo</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
              </select>
            </div>
            {task.dueDate && (
              <div className="text-sm text-gray-500">
                Due: {new Date(task.dueDate).toDateString()}
              </div>
            )}
          </div>
        </div>
      </div>

      {isExpanded && subtasks.length > 0 && (
        <div className="mt-2 space-y-2 relative">
          {/* Vertical connecting line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-base-300" />

          {subtasks.map((subtask) => (
            <div key={subtask.id} className="relative">
              {/* Horizontal connecting line */}
              <div className="absolute left-4 top-1/2 w-4 h-0.5 bg-base-300" />
              <SubtaskCard
                subtask={subtask}
                level={level + 1}
                parentId={task.id}
                onRefresh={() => {
                  fetchSubtasks();
                }}
                isDone={subtask.isDone}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
