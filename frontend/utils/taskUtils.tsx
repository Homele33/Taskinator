import apiClient from "@/api/axiosClient";
import { Task, Subtask } from "@/components/tasksTypes";

export const fetchTasks = async (): Promise<{ tasks: Task[] }> => {

  try {
    const response = await apiClient.get("/tasks");
    return response.data;
  }
  catch (error) {
    console.error("Error fetching tasks:", error);
    if (error.response) {
      console.error("Error status:", error.response.status);
      console.error("Error data:", error.response.data);
    }
    throw error; // Rethrow the error so the component can handle it
  }
};

export const createTask = async (taskData: Omit<Task, "id" | "subtasks">): Promise<Task> => {
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
    const response = await apiClient.post("/ai/parseTask", text)
    return response.data;
  }
  catch (error) {
    console.error("Error Creating NLP task from text::", error)
    throw error;
  }
}

export const deleteTask = async (taskId: string) => {
  try {
    const response = await apiClient.delete(`/tasks/${taskId}`);
    response.data;
  }
  catch (error) {
    console.error("Error deleting task:", error)
  }

}

export const addSubtask = async (taskId: string, subtaskData: Omit<Subtask, "id">): Promise<void> => {
  try {
    const response = await apiClient.post(`/tasks/subtasks/${taskId}`, subtaskData)
    if (response.status != 201) {
      console.log(response.data)
    }
  }
  catch (error) {
    console.error(error)
  }

}
