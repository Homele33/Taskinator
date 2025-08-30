import React, { useState, useEffect } from "react";
import TaskForm, { TaskFormData } from "@/components/taskForm";
import { Task } from "@/components/tasksTypes";
import { TaskCard } from "@/components/taskCard";
import { fetchTasks, createTask, updateTask } from "@/utils/taskUtils";
import { FuzzySearchBar } from "@/components/searchBar";
import NaturalLanguageTaskInput from "@/components/nlpInput";
import apiClient from "@/api/axiosClient";
import OnboardingModal from "@/components/OnboardingModal";

const MainPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    const theme = localStorage.getItem("theme") || "default";
    document.documentElement.setAttribute("data-theme", theme);
      (async () => {
        try {
          const res = await apiClient.get("/preferences");
          if (!res.data?.exists) {
            setShowOnboarding(true);
          }
        } catch (e) {
          console.error("Failed to check preferences:", e);
        }
      })();
    getTasks();
  }, []);

  const handleTaskSelect = (task: Task) => {
    setIsFormOpen(true);
    setEditingTask(task);
  };

  const getTasks = async () => {
    try {
      const data = await fetchTasks();
      setTasks(data.tasks);
      setError(null);
    } catch (err) {
      setError("Failed to load tasks. Please try again later.");
      console.error("Error fetching tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskSubmit = async (taskData: TaskFormData) => {
    if (editingTask) {
      await updateTask(taskData, editingTask.id);
      getTasks()
    }
    else {
       try {
      await createTask({
        ...taskData,
        scheduledStart: null,
        scheduledEnd: null,
      });
      setIsFormOpen(false);
      setEditingTask(undefined);
      await getTasks();
    } catch (error) {
      console.error("Error", error);

    }
  }


  const handleEditTask = (task: Task) => {
    setEditingTask(task);
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
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{error}</span>
          <button className="btn btn-sm" onClick={getTasks}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <FuzzySearchBar tasks={tasks} onTaskSelect={handleTaskSelect} />
        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingTask(undefined);
            setIsFormOpen(true);
          }}
          data-testid="new-task-button"
        >
          Add New Task
        </button>
        <OnboardingModal
          isOpen={showOnboarding}
          onClose={() => setShowOnboarding(false)}
          onSaved={() => {
            setShowOnboarding(false);
          }}
        />

        <TaskForm
          task={editingTask}
          isOpen={isFormOpen}
          onClose={() => {
            setIsFormOpen(false);
            setEditingTask(undefined);
          }}
          onSubmit={handleTaskSubmit}
        />
      </div>

      <NaturalLanguageTaskInput onTaskCreated={getTasks} />
      {
        tasks.length === 0 ? (
          <div className="text-center py-8" data-testid="task-list-empty">
            <p className="text-gray-500">
              No tasks found. Create your first task!
            </p>
          </div>
        ) : (
          <div className="space-y-4" data-testid="task-list">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onRefresh={getTasks}
                onEdit={handleEditTask}
                data-testid={`task-item-${task.id}`}
              />
            ))}
          </div>
        )
      }
    </div >
  );
};

export default MainPage;
