import React, { useState, useEffect } from "react";
import TaskForm, { TaskFormData } from "@/components/taskForm";
import { Task } from "@/components/task";
import { TaskCard } from "@/components/taskCard";

const MainPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [selectedParentId, setSelectedParentId] = useState<string | undefined>(
    undefined
  );

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/tasks");
      if (!response.ok) {
        throw new Error("Failed to fetch tasks");
      }
      const data = await response.json();
      setTasks(data.tasks);
      setError(null);
    } catch (err) {
      setError("Failed to load tasks. Please try again later.");
      console.error("Error fetching tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (taskData: TaskFormData) => {
    const response = await fetch("http://localhost:5000/api/create_task", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(taskData),
    });

    if (!response.ok) {
      throw new Error("Failed to create task");
    }

    fetchTasks();
  };

  const handleUpdateTask = async (taskId: string, taskData: TaskFormData) => {
    const response = await fetch(
      `http://localhost:5000/api/${taskId}/update_task`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(taskData),
      }
    );

    if (!response.ok) {
      throw new Error("Failed to update task");
    }

    fetchTasks();
  };

  const handleFormSubmit = async (taskData: TaskFormData) => {
    if (editingTask) {
      await handleUpdateTask(editingTask.id, taskData);
    } else {
      await handleCreateTask(taskData);
    }
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setSelectedParentId(undefined);
    setIsFormOpen(true);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div role="alert" className="alert alert-error">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="stroke-current shrink-0 h-6 w-6"
            fill="none"
            viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{error}</span>
          <button className="btn btn-sm" onClick={fetchTasks}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  function handleStatusChange(taskId: string, newStatus: string): void {
    throw new Error(`Function not implemented. ${taskId} ${newStatus}`);
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Tasks</h1>
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingTask(undefined);
            setSelectedParentId(undefined);
            setIsFormOpen(true);
          }}>
          Add New Task
        </button>

        <TaskForm
          task={editingTask}
          parentTaskId={selectedParentId}
          isOpen={isFormOpen}
          onClose={() => {
            setIsFormOpen(false);
            setEditingTask(undefined);
            setSelectedParentId(undefined);
          }}
          onSubmit={handleFormSubmit}
        />
      </div>

      {tasks.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500">
            No tasks found. Create your first task!
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onStatusChange={handleStatusChange}
              onRefresh={fetchTasks}
              onEdit={handleEditTask}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MainPage;
