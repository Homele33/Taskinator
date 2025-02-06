import React, { useEffect, useState } from "react";
import { Subtask } from "./task";

interface SubtaskCardProps {
  subtask: Subtask;
  level?: number;
  parentId: string;
  isDone: boolean;
  onDelete: (subtaskId: string) => void;
  onRefresh: () => void;
}

const getCardStyles = () => {
  const baseStyles = "card shadow-lg hover:shadow-xl transition-shadow";

  return `${baseStyles} scale-90 opacity-90 border-l-4 border-l-base-300`;
};

export const SubtaskCard: React.FC<SubtaskCardProps> = ({
  subtask,
  level = 1,
  onDelete,
  onRefresh,
  isDone = false,
}) => {
  const handleDeleteSubtask = async (id: string) => {
    const response = await fetch(
      `http://localgost:5000/api/${subtask.parentId}/${id}/delete_subtask`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to delete subtask");
    }
    onRefresh();
  };

  const handleEditSubtask = async (subtask: Subtask) => {
    throw new Error("Function not implemented.");
  };

  return (
    <div className={`ml-${level * 12}`}>
      <div className={`${getCardStyles}`}>
        <div className="card-body">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold">{subtask.title}</h2>
              
            </div>
            
            <div className="flex gap-2">
                
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
                    <button onClick={() => handleEditSubtask(subtask)}>
                      Edit
                    </button>
                  </li>
                  <li>
                    <button onClick={() => handleDeleteSubtask(subtask.id)}>
                      Delete
                    </button>
                  </li>
                </ul>
                
              </div>
              
            </div>
            
          </div>
          <p className="text-gray-600">{subtask.description}</p>
        </div>
      </div>
      
    </div>
  );
};
