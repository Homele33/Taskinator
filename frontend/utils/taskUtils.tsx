import apiClient from "@/api/axiosClient";
import { Task, Subtask } from "@/components/tasksTypes";
import { error } from "console";

export const fetchTasks = async (): Promise<{ tasks: Task[] }> => {
  try {
    const response = await apiClient.get("/tasks");
    return response.data;
  } catch (error: any) {
    if (error.status === 401) {
      if (typeof window !== undefined) {
        window.location.href = "/login";
      }

    }
    throw error; // Rethrow the error so the component can handle it
  }
};

type CreateTaskPayload = Omit<Task, "id" | "subtasks"> & {
  durationMinutes: number;           
  scheduledStart?: string | null;    
  scheduledEnd?: string | null;      
};

export const createTask = async (
  taskData: CreateTaskPayload
): Promise<Task> => {
  if (
    taskData.durationMinutes === undefined ||
    taskData.durationMinutes === null ||
    Number.isNaN(Number(taskData.durationMinutes))
  ) {
    throw new Error("durationMinutes is required and must be a number");
  }

  const payload = {
    ...taskData,
    scheduledStart: taskData.scheduledStart ?? null,
    scheduledEnd: taskData.scheduledEnd ?? null,
  };

  try {
    const response = await apiClient.post("/tasks", payload);
    return response.data;
  } catch (error) {
    console.error("Error creating task:", error);
    throw error;
  }
};


export const createNlpTask = async (text: string): Promise<Task> => {
  try {
    const response = await apiClient.post("/ai/parseTask", text);
    return response.data;
  } catch (error) {
    console.error("Error Creating NLP task from text::", error);
    throw error;
  }
};

export const deleteTask = async (taskId: string) => {
  try {
    const response = await apiClient.delete(`/tasks/${taskId}`);
    response.data;
  } catch (error) {
    console.error("Error deleting task:", error);
  }
};

export const addSubtask = async (
  taskId: string,
  subtaskData: Omit<Subtask, "id">
): Promise<void> => {
  try {
    const response = await apiClient.post(
      `/tasks/subtasks/${taskId}`,
      subtaskData
    );
    if (response.status != 201) {
      console.log(response.data);
    }
  } catch (error) {
    console.error(error);
  }
};

export const deleteSubtask = async (
  taskId: string,
  subtasksId: string
): Promise<void> => {
  try {
    const response = await apiClient.delete(
      `/tasks/subtasks/${taskId}/${subtasksId}`
    );
    if (response.status != 200) {
      console.log(response.data);
    }
  } catch (error) {
    console.error(error);
  }
};

export const toggleSubtask = async (
  taskId: string,
  subtaskId: string
): Promise<void> => {
  try {
    const response = await apiClient.patch(
      `/tasks/subtasks/${taskId}/${subtaskId}`
    );
    if (response.status != 200) {
    }
  } catch {
    console.error("Error toggeling subtask");
  }
};

export const updateSubtask = async (
  subtaskData: Omit<Subtask, "id">,
  parentId: string,
  id: string
) => {
  try {
    const response = await apiClient.put(`/tasks/subtasks/${parentId}/${id}`, subtaskData)
    if (response.status !== 200) {
      console.error("Error updating subtask: ", response.data)
    }
  }
  catch (error) {
    console.error("Unexpected error: ", error);
  }
}

export const submitPreferences = async (preferences: any): Promise<void> => {
  try {
    const response = await apiClient.post("/preferences", preferences);
    if (response.status !== 200) {
      console.error("Error submitting preferences:", response.data);
    }
  } catch (error) {
    console.error("Error submitting preferences:", error);
    throw error;
  }
};

export const updateTask = async (taskData: Omit<Task, "id" | "subtasks">, id: string): Promise<Task> => {
  try {
    const response = await apiClient.patch(`/tasks/${id}`, taskData)
    if (response.status !== 200) {
      console.error("Error updating task: ", response.data)
    }
    return response.data
  }
  catch (error) {
    console.error("Unexpected error updating task");
    throw error;
  }
}

export const changeTaskStatus = async (newStatus: string, id: string) => {
  const response = await apiClient.put(`/tasks/${id}`, newStatus)
  if (response.status !== 200) {
    console.error("error updating status")
  }
}

