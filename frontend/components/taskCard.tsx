import React, { useState, useEffect } from "react";
import { Subtask, Task } from "./tasksTypes";
import SubtaskForm, { SubtaskFormData } from "./subtaskForm";
import { SubtaskCard } from "./subtaskCard";
import {
  Pencil,
  Trash2,
  SquarePlus,
  EllipsisVertical,
  Bot,
} from "lucide-react";
import { deleteTask, addSubtask, updateSubtask, changeTaskStatus } from "@/utils/taskUtils";
import apiClient from "@/api/axiosClient";

interface TaskCardProps {
  task: Task;
  onRefresh: () => void;
  onEdit: (task: Task) => void;
}

const getCardStyles = () => {
  // Base styles for all cards
  const baseStyles = "card shadow-lg hover:shadow-xl transition-shadow";

  return `${baseStyles} `;
};

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onRefresh,
  onEdit,
  ...props
}) => {
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoadingSubtasks, setIsLoadingSubtasks] = useState(false);
  const [editSubtask, setEditingSubtask] = useState<Subtask | undefined>(undefined);
  const [isFormOpen, setIsFormOpen] = useState(false);


  useEffect(() => {
    onRefresh;
  }, [onRefresh, subtasks]);

  const fetchSubtasks = async () => {
    setIsLoadingSubtasks(true);
    try {
      const response = await apiClient.get(`/tasks/subtasks/${task.id}`);
      setSubtasks(response.data);
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

  const handleDeleteTask = async (id: string) => {
    try {
      const response = deleteTask(id);
      await response;
    } catch (error) {
      console.error("error:", error);
    }
    onRefresh();
  };

  const handleSubmitSubtask = async (subtask: SubtaskFormData) => {
    if (editSubtask) {
      updateSubtask(subtask, task.id, editSubtask.id)
      onRefresh();
      fetchSubtasks();
      setIsExpanded(true);

    }
    else {
      addSubtask(task.id, subtask);
      await fetchSubtasks();
      onRefresh();
      setIsExpanded(true);
    }
  }

  const handleEditSubtask = async (subtask: Subtask) => {
    setEditingSubtask(subtask);
    setIsFormOpen(true);
  }

  const handleStatusChange = async (id: string, newStatus: string) => {
    await changeTaskStatus(newStatus, id)
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
    <div className={``} {...props}>
      <div className={`${getCardStyles()} bg-base-300`}>
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
                      className={`h-4 w-4 transition-transform ${isExpanded ? "rotate-90" : ""
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
                className={`${"text-xl"} font-bold  text-primary`}
                data-testid={`task-title-${task.id}`}
              >
                {task.title.substring(0, 100)}
              </h2>
            </div>
            <div className="flex gap-2">
              <span className={`badge ${getPriorityColor(task.priority)}`} data-testid={`task-priority-${task.id}`}>
                {task.priority}
              </span>
              <span className="badge text-primary" data-testid={`task-type-${task.id}`}>
                {task.task_type}
              </span>
              <div className="dropdown " data-testid={`task-menu-${task.id}`}>
                <div>
                  <label
                    tabIndex={0}
                    className="text-primary btn btn-ghost btn-circle btn-sm "
                  >
                    <EllipsisVertical />
                  </label>
                </div>

                <ul
                  tabIndex={0}
                  className="dropdown-content menu p-2 shadow bg-accent-content rounded-box absolute"
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
                        data-testid={`task-add-subtask-${task.id}`}
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
                        data-testid={`task-delete-button-${task.id}`}
                        className="btn btn-ghost btn-md text-error"
                      >
                        <Trash2 /> {/* Delete icon*/}
                      </button>
                    </li>
                  </div>
                </ul>
                <SubtaskForm
                  subtask={editSubtask}
                  parentId={task.id}
                  isOpen={isFormOpen}
                  onClose={() => {
                    setIsFormOpen(false);
                    setEditingSubtask(undefined);
                  }}
                  onSubmit={handleSubmitSubtask}
                />
              </div>
            </div>
          </div>

          <p className="text-accent" data-testid={`task-description-${task.id}`}>{task.description}</p>

          <div className="flex justify-between items-center mt-4">
            <div className="flex items-center gap-2">
              <select
                className={`select select-bordered select-sm text-base-100 ${{
                  TODO: "bg-primary",
                  IN_PROGRESS: "bg-info",
                  COMPLETED: "bg-success",
                }[task.status]
                  }`}
                value={task.status}
                data-testid={`task-status-${task.id}`}
                onChange={(e) => handleStatusChange(task.id, e.target.value)}
              >
                <option value="TODO">Todo</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
              </select>
            </div>
            {task.dueDate && (
              <div className="text-sm text-accent" data-testid={`task-datetime-${task.id}`}>
                Due: {new Date(task.dueDate).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      </div>

      {
        isExpanded && subtasks.length > 0 && (
          <div className="mt-2 space-y-2">
            {subtasks.map((subtask) => (
              <div
                key={subtask.id}
                className=" "
                data-testid={`subtask-list-${task.id}`}
              >
                <SubtaskCard
                  subtask={subtask}
                  parentId={task.id}
                  onRefresh={() => {
                    fetchSubtasks();
                  }}
                  isDone={subtask.isDone}
                  onEdit={handleEditSubtask}
                />
              </div>
            ))}
          </div>
        )
      }
    </div >
  );
};
