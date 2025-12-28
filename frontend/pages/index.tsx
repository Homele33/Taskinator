import React, { useState, useEffect } from "react";
import TaskForm, { TaskFormData } from "@/components/taskForm";
import { Task } from "@/components/tasksTypes";
import { TaskCard } from "@/components/taskCard";
import { fetchTasks, createTask, updateTask } from "@/utils/taskUtils";
import { FuzzySearchBar } from "@/components/searchBar";
import NaturalLanguageTaskInput from "@/components/nlpInput";
import apiClient from "@/api/axiosClient";
import OnboardingModal from "@/components/OnboardingModal";
import ConflictResolverModal from "@/components/ConflictResolverModal";
import SuggestionSelectionModal from "@/components/SuggestionSelectionModal";
import { isAxiosError } from "axios";

const MainPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Conflict resolution state
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [showSuggestionModal, setShowSuggestionModal] = useState(false);
  const [conflictSuggestions, setConflictSuggestions] = useState<any[]>([]);
  const [pendingTaskData, setPendingTaskData] = useState<TaskFormData | null>(null);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [suggestionPage, setSuggestionPage] = useState(1);
  const [currentStrategy, setCurrentStrategy] = useState<"day" | "week" | "month" | "auto" | null>(null);

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
    console.log("[TASK FETCH] ============================================");
    console.log("[TASK FETCH] getTasks() called - fetching from server...");
    try {
      const data = await fetchTasks();
      console.log("[TASK FETCH] Received response from server");
      console.log("[TASK FETCH] Total tasks:", data.tasks?.length || 0);
      console.log("[TASK FETCH] Task IDs:", data.tasks?.map((t: Task) => t.id));
      console.log("[TASK FETCH] Task details:");
      data.tasks?.forEach((task: Task, idx: number) => {
        console.log(`[TASK FETCH]   Task ${idx + 1} (ID: ${task.id}):`);
        console.log(`[TASK FETCH]     - Title: ${task.title}`);
        console.log(`[TASK FETCH]     - Due Date: ${task.dueDate}`);
        console.log(`[TASK FETCH]     - Scheduled Start: ${task.scheduledStart}`);
      });
      
      console.log("[TASK FETCH] Setting tasks state...");
      setTasks(data.tasks);
      setError(null);
      console.log("[TASK FETCH] ✅ Tasks state updated successfully");
    } catch (err) {
      console.error("[TASK FETCH] ❌ Error fetching tasks:", err);
      setError("Failed to load tasks. Please try again later.");
    } finally {
      setLoading(false);
      console.log("[TASK FETCH] ============================================");
    }
  };

const handleTaskSubmit = async (taskData: TaskFormData) => {
    try {
      if (editingTask) {
        await updateTask(taskData, editingTask.id);
      } else {
        await createTask({
          ...taskData,
          scheduledStart: null,
          scheduledEnd: null,
        });
      }
      
      setIsFormOpen(false);
      setEditingTask(undefined);
      await getTasks();
    } catch (error: any) {
      // Handle 409 Conflict - time slot already occupied (SILENT, NO ALERTS)
      // Check multiple possible locations for the status code
      const status = error?.response?.status || error?.status;
      const isConflict = status === 409 || 
                        error?.response?.data?.status === "conflict" ||
                        (error?.message && error.message.includes("409"));
      
      if (isConflict) {
        console.log("✅ [CONFLICT] Detected in manual task creation - triggering resolution flow");
        setPendingTaskData(taskData);
        setShowConflictModal(true);
        setIsFormOpen(false); // Close the task form
        setEditingTask(undefined); // Clear editing state
        return; // Silent return - no error alert
      }
      
      // Only show alert for non-conflict errors
      console.error("❌ Error submitting task:", error);
      alert("Failed to create task. Please try again.");
    }
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setIsFormOpen(true);
  };

  // Handle conflict resolution strategy selection
  const handleConflictStrategy = async (strategy: "day" | "week" | "month" | "auto") => {
    if (!pendingTaskData) return;

    // Reset pagination when selecting new strategy
    setSuggestionPage(1);
    setCurrentStrategy(strategy);
    setIsLoadingSuggestions(true);
    setShowConflictModal(false);

    try {
      // CRITICAL FIX: Extract date from task data, priority: scheduledStart > dueDate > now
      let referenceDate = new Date().toISOString();
      const taskAsAny = pendingTaskData as any;
      
      if (taskAsAny.scheduledStart) {
        referenceDate = new Date(taskAsAny.scheduledStart).toISOString();
        console.log("[CONFLICT] Using scheduledStart:", referenceDate);
      } else if (pendingTaskData.dueDate) {
        referenceDate = new Date(pendingTaskData.dueDate).toISOString();
        console.log("[CONFLICT] Using dueDate:", referenceDate);
      } else {
        console.log("[CONFLICT] No date in task, using current time:", referenceDate);
      }

      // Ensure durationMinutes is a valid number
      const duration = Number(pendingTaskData.durationMinutes) || 60;

      console.log("[DEBUG] Fetching suggestions with:", {
        durationMinutes: duration,
        task_type: pendingTaskData.task_type,
        strategy: strategy,
        referenceDate: referenceDate,
      });

      const res = await apiClient.post("/ai/suggest?page=1", {
        durationMinutes: duration,
        task_type: pendingTaskData.task_type || "Meeting",
        strategy: strategy,
        referenceDate: referenceDate,
        pageSize: 3,  // UX: Show top 3 scored suggestions per page
        // CRITICAL FIX: Pass task date fields for backend extraction
        scheduledStart: (pendingTaskData as any).scheduledStart || null,
        scheduledEnd: (pendingTaskData as any).scheduledEnd || null,
        dueDate: pendingTaskData.dueDate || null,
      });

      const data = res.data;
      if (Array.isArray(data?.suggestions) && data.suggestions.length > 0) {
        setConflictSuggestions(data.suggestions);
        setShowSuggestionModal(true);
      } else {
        alert("No available time slots found for the selected strategy.");
        setShowConflictModal(true); // Re-show conflict modal
      }
    } catch (err: any) {
      console.error("Failed to fetch conflict resolution suggestions:", err);
      console.error("Error details:", err?.response?.data);
      alert("Failed to fetch alternative time slots. Please try again.");
      setShowConflictModal(true); // Re-show conflict modal
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  // Handle suggestion selection and retry task creation
  const handleSuggestionSelect = async (suggestion: any) => {
    console.log("🔵 [HANDLER] handleSuggestionSelect CALLED!");
    console.log("🔵 [HANDLER] Function received suggestion:", suggestion);
    console.log("🔵 [HANDLER] Current pendingTaskData:", pendingTaskData);
    console.log("🔵 [HANDLER] pendingTaskData is null?", pendingTaskData === null);
    
    if (!pendingTaskData) {
      console.error("🔴 [HANDLER] No pendingTaskData available - EXITING EARLY!");
      return;
    }
    
    console.log("✅ [HANDLER] pendingTaskData exists, proceeding...");

    try {
      console.log("[DEBUG] Attempting to create task with merged data...");
      
      // Merge pending task data with selected time slot
      const taskPayload = {
        ...pendingTaskData,
        scheduledStart: suggestion.scheduledStart,
        scheduledEnd: suggestion.scheduledEnd,
      };
      
      console.log("[DEBUG] Task payload:", taskPayload);
      
      await createTask(taskPayload);

      console.log("[DEBUG] ✅ Task created successfully!");
      
      // Success - close all modals and refresh
      setShowSuggestionModal(false);
      setIsFormOpen(false);
      setPendingTaskData(null);
      setConflictSuggestions([]);
      setSuggestionPage(1);
      setCurrentStrategy(null);
      await getTasks();
    } catch (err: any) {
      console.error("[DEBUG] ❌ Error creating task with suggestion:", err);
      console.error("[DEBUG] Error details:", err?.response?.data);
      alert("Failed to create task. Please try again.");
    }
  };

  // Handle refresh/pagination for suggestions (Next)
  const handleRefreshSuggestions = async () => {
    console.log("🟢 [NEXT] handleRefreshSuggestions CALLED!");
    console.log("🟢 [NEXT] Current pendingTaskData:", pendingTaskData);
    console.log("🟢 [NEXT] Current strategy:", currentStrategy);
    console.log("🟢 [NEXT] Current page:", suggestionPage);
    
    if (!pendingTaskData || !currentStrategy) {
      console.error("🔴 [NEXT] Missing pendingTaskData or currentStrategy - EXITING!");
      return;
    }
    
    console.log("✅ [NEXT] Prerequisites met, proceeding...");

    const nextPage = suggestionPage + 1;
    setIsLoadingSuggestions(true);

    try {
      // CRITICAL FIX: Extract date from task data, priority: scheduledStart > dueDate > now
      let referenceDate = new Date().toISOString();
      const taskAsAny = pendingTaskData as any;
      
      if (taskAsAny.scheduledStart) {
        referenceDate = new Date(taskAsAny.scheduledStart).toISOString();
      } else if (pendingTaskData.dueDate) {
        referenceDate = new Date(pendingTaskData.dueDate).toISOString();
      }

      const duration = Number(pendingTaskData.durationMinutes) || 60;

      console.log("[DEBUG] Fetching page", nextPage);

      const res = await apiClient.post(`/ai/suggest`, {
        durationMinutes: duration,
        task_type: pendingTaskData.task_type || "Meeting",
        strategy: currentStrategy,
        referenceDate: referenceDate,
        page: nextPage,  // CRITICAL: Pass page in body, not query string
        pageSize: 3,  // UX: Show top 3 scored suggestions per page
        // CRITICAL FIX: Pass task date fields for backend extraction
        scheduledStart: (pendingTaskData as any).scheduledStart || null,
        scheduledEnd: (pendingTaskData as any).scheduledEnd || null,
        dueDate: pendingTaskData.dueDate || null,
      });

      const data = res.data;
      if (Array.isArray(data?.suggestions) && data.suggestions.length > 0) {
        // FIX: REPLACE suggestions for strict pagination (don't append)
        setConflictSuggestions(data.suggestions);
        setSuggestionPage(nextPage);
        console.log("[DEBUG] Loaded page", nextPage, "with", data.suggestions.length, "suggestions");
      } else {
        alert("No more suggestions available.");
      }
    } catch (err: any) {
      console.error("Failed to fetch more suggestions:", err);
      alert("Failed to fetch more suggestions. Please try again.");
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  // Handle previous page navigation
  const handlePreviousSuggestions = async () => {
    console.log("🔵 [PREVIOUS] handlePreviousSuggestions CALLED!");
    console.log("🔵 [PREVIOUS] Current page:", suggestionPage);
    
    if (suggestionPage <= 1) {
      console.error("🔴 [PREVIOUS] Already at page 1 - EXITING!");
      return;
    }
    
    if (!pendingTaskData || !currentStrategy) {
      console.error("🔴 [PREVIOUS] Missing pendingTaskData or currentStrategy - EXITING!");
      return;
    }
    
    console.log("✅ [PREVIOUS] Prerequisites met, proceeding...");

    const prevPage = suggestionPage - 1;
    setIsLoadingSuggestions(true);

    try {
      // CRITICAL FIX: Extract date from task data, priority: scheduledStart > dueDate > now
      let referenceDate = new Date().toISOString();
      const taskAsAny = pendingTaskData as any;
      
      if (taskAsAny.scheduledStart) {
        referenceDate = new Date(taskAsAny.scheduledStart).toISOString();
      } else if (pendingTaskData.dueDate) {
        referenceDate = new Date(pendingTaskData.dueDate).toISOString();
      }

      const duration = Number(pendingTaskData.durationMinutes) || 60;

      console.log("[DEBUG] Fetching page", prevPage);

      const res = await apiClient.post(`/ai/suggest`, {
        durationMinutes: duration,
        task_type: pendingTaskData.task_type || "Meeting",
        strategy: currentStrategy,
        referenceDate: referenceDate,
        page: prevPage,  // CRITICAL: Pass page in body, not query string
        pageSize: 3,  // UX: Show top 3 scored suggestions per page
        // CRITICAL FIX: Pass task date fields for backend extraction
        scheduledStart: (pendingTaskData as any).scheduledStart || null,
        scheduledEnd: (pendingTaskData as any).scheduledEnd || null,
        dueDate: pendingTaskData.dueDate || null,
      });

      const data = res.data;
      if (Array.isArray(data?.suggestions) && data.suggestions.length > 0) {
        setConflictSuggestions(data.suggestions);
        setSuggestionPage(prevPage);
        console.log("[DEBUG] Loaded page", prevPage, "with", data.suggestions.length, "suggestions");
      } else {
        alert("No suggestions available for this page.");
      }
    } catch (err: any) {
      console.error("Failed to fetch previous suggestions:", err);
      alert("Failed to fetch previous suggestions. Please try again.");
    } finally {
      setIsLoadingSuggestions(false);
    }
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

      {/* Conflict Resolution Modal */}
      <ConflictResolverModal
        isOpen={showConflictModal}
        onClose={() => {
          setShowConflictModal(false);
          // FIX: Don't clear pendingTaskData here - it needs to survive
          // the transition to SuggestionSelectionModal
        }}
        onResolve={handleConflictStrategy}
      />

      {/* Suggestion Selection Modal */}
      {/* DEBUG: Log modal props before rendering */}
      {showSuggestionModal && (() => {
        console.log("📦 [MODAL PROPS]", {
          isOpen: showSuggestionModal,
          suggestionsCount: conflictSuggestions.length,
          isLoading: isLoadingSuggestions,
          hasPendingTaskData: !!pendingTaskData,
          hasOnSelect: typeof handleSuggestionSelect === 'function',
          hasOnRefresh: typeof handleRefreshSuggestions === 'function'
        });
        return null;
      })()}
      <SuggestionSelectionModal
        isOpen={showSuggestionModal}
        onClose={() => {
          setShowSuggestionModal(false);
          setConflictSuggestions([]);
          setSuggestionPage(1);
          setCurrentStrategy(null);
          // FIX: Clear pendingTaskData HERE when user cancels the whole flow
          setPendingTaskData(null);
        }}
        suggestions={conflictSuggestions}
        onSelect={handleSuggestionSelect}
        isLoading={isLoadingSuggestions}
        metadata={pendingTaskData ? {
          title: pendingTaskData.title,
          task_type: pendingTaskData.task_type,
          priority: pendingTaskData.priority,
          durationMinutes: pendingTaskData.durationMinutes,
        } : null}
        page={suggestionPage}
        onRefresh={handleRefreshSuggestions}
        onPrevious={handlePreviousSuggestions}
        onBackToOptions={() => {
          console.log("[MANUAL FLOW] User requested back to strategy selection");
          setShowSuggestionModal(false);
          setConflictSuggestions([]);
          setSuggestionPage(1);
          setCurrentStrategy(null);
          setShowConflictModal(true); // Re-show strategy selection
        }}
        hasMorePages={conflictSuggestions.length >= 3}
        isConflict={true} // This is a conflict resolution flow
      />

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
