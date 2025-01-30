// tasks api
export const getTasks = async () => {
  // get all tasks
  const response = await fetch("http://localhost:5000/api/tasks");
  if(!response.ok) throw new Error("Failed to fetch tasks");

  return response.json();
}

export const createTask = async (taskData: TaskFormData) => {
  
}