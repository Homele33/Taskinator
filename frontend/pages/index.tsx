import React, { useState, useEffect } from 'react';

interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'TODO' | 'IN_PROGRESS' | 'COMPLETED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  due_date?: string;
  subTasks: Array<any>;
}

interface TaskCardProps {
  task: Task;
  level?: number;
  onStatusChange: (taskId: string, newStatus: string) => void;
}

const getCardStyles = (level: number) => {
  // Base styles for all cards
  const baseStyles = "card shadow-lg hover:shadow-xl transition-shadow";
  
  // Additional styles for subtasks
  if (level > 0) {
    return `${baseStyles} scale-95 opacity-90`;
  }
  
  return baseStyles;
};

const TaskCard: React.FC<TaskCardProps> = ({ task, level = 0, onStatusChange }) => {
  const [subtasks, setSubtasks] = useState<Task[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoadingSubtasks, setIsLoadingSubtasks] = useState(false);

  const toggleSubtasks = () =>{
    if (!isExpanded) {
      setIsLoadingSubtasks(true);

      setSubtasks(task.subTasks);
      
      setIsLoadingSubtasks(false);  
      
    }
    // show or hide subtasks 
    setIsExpanded(!isExpanded);

  };
  
    

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'HIGH':
        return 'badge-error';
      case 'MEDIUM':
        return 'badge-warning';
      case 'LOW':
        return 'badge-info';
      default:
        return 'badge-ghost';
    }
  };

  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'TODO':
        return 'bg-base-200';
      case 'IN_PROGRESS':
        return 'bg-blue-50';
      case 'COMPLETED':
        return 'bg-green-50';
      default:
        return 'bg-base-200';
    }
  };

  return (
    <div className={`ml-${level * 8}`}>
      <div className={`${getCardStyles(level)} ${getStatusColor(task.status)}`}>
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              {task.subTasks && (
                <button 
                  onClick={toggleSubtasks}
                  className="btn btn-ghost btn-sm btn-circle"
                >
                  {isLoadingSubtasks ? (
                    <span className="loading loading-spinner loading-xs"></span>
                  ) : (
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  )}
                </button>
              )}
              <h2 className={`${level > 0 ? 'text-lg' : 'text-xl'} font-bold`}>{task.title}</h2>
            </div>
            <div className="flex gap-2">
              <span className={`badge ${getPriorityColor(task.priority)}`}>
                {task.priority}
              </span>
              <div className="dropdown dropdown-end">
                <label tabIndex={0} className="btn btn-ghost btn-circle btn-sm">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                  </svg>
                </label>
                <ul tabIndex={0} className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
                  <li><button>Edit</button></li>
                  <li><button>Add Subtask</button></li>
                  <li><button>Delete</button></li>
                </ul>
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
            {task.due_date && (
              <div className="text-sm text-gray-500">
                Due: {new Date(task.due_date).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {isExpanded && subtasks.length > 0 && (
        <div className="mt-2 space-y-2">
          {subtasks.map((subtask) => (
            <TaskCard
              key={subtask.id}
              task={subtask}
              level={level + 1}
              onStatusChange={onStatusChange}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const MainPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/tasks');
      if (!response.ok) {
        throw new Error('Failed to fetch tasks');
      }
      const data = await response.json();
      setTasks(data.tasks);
      setError(null);
    } catch (err) {
      setError('Failed to load tasks. Please try again later.');
      console.error('Error fetching tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update task status');
      }
      
      // Refresh tasks after update
      fetchTasks();
    } catch (err) {
      console.error('Error updating task status:', err);
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
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
          <button className="btn btn-sm" onClick={fetchTasks}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Tasks</h1>
        <button className="btn btn-primary">
          Add New Task
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500">No tasks found. Create your first task!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MainPage;