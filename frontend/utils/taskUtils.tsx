export const fetchTasks= async() => {
    try {
        const response = await fetch(`http://localhost:5000/api/tasks`);
        if (!response.ok) {
            throw new Error("Failed to fetch tasks");
        }
        
        return response.json();
    } catch (err) {
        console.error("Error fetching tasks:", err);
    }
}