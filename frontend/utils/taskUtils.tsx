import apiClient from "@/api/axiosClient";
import { Task, Subtask } from "@/components/tasksTypes";

export const fetchTasks = async (): Promise<{ tasks: Task[] }> => {
  try {
    const response = await apiClient.get("/tasks");
    return response.data;
  } catch (error: any) {
    if (error.status === 401) {
      if (typeof window !== "undefined") {
        // Redirect to login page if the user is not authenticated
        window.location.href = "/login";
      }
      return { tasks: [] }; // Return an empty array if the user is not authenticated
    }
    throw error; // Rethrow the error so the component can handle it
  }
};

export const createTask = async (
  taskData: Omit<Task, "id" | "subtasks">
): Promise<Task> => {
  try {
    const response = await apiClient.post("/tasks", taskData);
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
