import React, { useState, useEffect } from "react";
import { Task } from "./task";
import SubtaskForm, {SubtaskFormData} from "./subtaskForm";

interface TaskCardProps {
  task: Task;
  level?: number;
  onStatusChange: (taskId: string, newStatus: string) => void;
  onDelete: (taskId: string) => void;
  onRefresh: () => void;
}

const getCardStyles = (level: number) => {
  // Base styles for all cards
  const baseStyles = "card shadow-lg hover:shadow-xl transition-shadow";

  // Additional styles for subtasks - including border styles
  if (level > 0) {
    return `${baseStyles} scale-95 opacity-90 border-l-4 border-l-base-300`;
  }

  return `${baseStyles} border border-base-200`;
};

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  level = 0,
  onStatusChange,
  onDelete,
  onRefresh,
}) => {
  const [subtasks, setSubtasks] = useState<Task[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoadingSubtasks, setIsLoadingSubtasks] = useState(false);
  const [editSubtask, setEditingSubtask] = useState<string | undefined>(undefined);
  const [selectedParentId, setSelectedParentId] = useState<string | undefined>(undefined);
  const [isFormOpen, setIsFormOpen] = useState(false);

  const fetchSubtasks = async () => {
    if (!isExpanded) {
      setIsLoadingSubtasks(true);
      try {
        const response = await fetch(
          `http://localhost:5000/api/${task.id}/subtasks`
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
    }
    setIsExpanded(!isExpanded);
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

  function handleEditTask(task: Task): void {
    throw new Error("Function not implemented.");
  }

  const handleAddSubtask = async(subtask: SubtaskFormData) => {
    const response = await fetch(`http://localhost:5000/api/${subtask.parentId}/add_subtask`,{
      method: "POST",
      headers:{
        "Content-Type": "application/json",
      },
      body: JSON.stringify(subtask)
    } );
    if (!response.ok){
      throw new Error("Failed to create subtask");
    }
  }

  const handleDeleteTask = async (id: string) => {
    const response = await fetch(
      `http://localhost:5000/api/${id}/delete_task`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to delete task");
    }
    onRefresh();
  };

  return (
    <div className={`ml-${level * 12}`}>
      <div className={`${getCardStyles(level)} ${getStatusColor(task.status)}`}>
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              {task.subTasks && (
                <button
                  onClick={fetchSubtasks}
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
              <div className="dropdown dropdown-end">
                <label tabIndex={0} className="btn btn-ghost btn-circle btn-sm">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z"
                    />
                  </svg>
                </label>
                <ul
                  tabIndex={0}
                  className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52"
                >
                  <li>
                    <button onClick={() => handleEditTask(task)}>Edit</button>
                  </li>
                  <li>
                    <button onClick={() => {
                      setIsFormOpen(true)
                      setEditingSubtask(undefined)
                      setSelectedParentId(task.id)
                    }}
                      >
                      Add Subtask
                    </button>
                  </li>
                  <li>
                    <button onClick={() => handleDeleteTask(task.id)}>
                      Delete
                    </button>
                  </li>
                </ul>
                <SubtaskForm 
                subtask={undefined} 
                parentId={task.id} 
                isOpen={isFormOpen} 
                onClose={() =>{
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
                onChange={(e) => onStatusChange(task.id, e.target.value)}
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

          {subtasks.map((subtask, index) => (
            <div key={subtask.id} className="relative">
              {/* Horizontal connecting line */}
              <div className="absolute left-4 top-1/2 w-4 h-0.5 bg-base-300" />
              <TaskCard
                task={subtask}
                level={level + 1}
                onStatusChange={onStatusChange}
                onDelete={onDelete}
                onRefresh={onRefresh}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
