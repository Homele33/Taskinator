"use client";

import { useState, useEffect, ReactNode } from "react";
import { Task } from "./task";

// Fuzzy search implementation
const fuzzySearch = (items: Task[], query: string): Task[] => {
  if (!query || query.trim() === "") {
    return items;
  }

  const lowercaseQuery = query.toLowerCase();

  return items.filter((item) => {
    const itemText = item.title.toLowerCase();

    // Check if all characters in query exist in the item title in the right order
    let idx = 0;
    for (const char of lowercaseQuery) {
      idx = itemText.indexOf(char, idx);
      if (idx === -1) return false;
      idx += 1;
    }

    return true;
  });
};

interface FuzzySearchBarProps {
  tasks: Task[];
  onTaskSelect: (task: Task) => void;
}

export const FuzzySearchBar = ({
  tasks,
  onTaskSelect,
}: FuzzySearchBarProps) => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filteredTasks, setFilteredTasks] = useState<Task[]>(tasks);

  // Update filtered tasks when search query changes
  useEffect(() => {
    setFilteredTasks(fuzzySearch(tasks, searchQuery));
  }, [searchQuery, tasks]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const highlightMatch = (text: string, query: string): ReactNode => {
    if (!query) return text;

    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();

    const result: ReactNode[] = [];
    let lastIndex = 0;
    let currentQueryIndex = 0;

    for (let i = 0; i < lowerText.length; i++) {
      if (
        currentQueryIndex < lowerQuery.length &&
        lowerText[i] === lowerQuery[currentQueryIndex]
      ) {
        // Add non-matching text before this match
        if (i > lastIndex) {
          result.push(text.substring(lastIndex, i));
        }

        // Add highlighted character
        result.push(
          <span key={i} className="text-accent text-2xl">
            {text[i]}
          </span>
        );

        lastIndex = i + 1;
        currentQueryIndex++;
      }
    }

    // Add remaining text
    if (lastIndex < text.length) {
      result.push(
        <span className="text-base-content"> {text.substring(lastIndex)}</span>
      );
    }

    return result;
  };

  // Function to determine the status badge color
  const getStatusBadgeColor = (status: Task["status"]): string => {
    switch (status) {
      case "TODO":
        return "bg-gray-200 text-gray-800";
      case "IN_PROGRESS":
        return "bg-blue-200 text-blue-800";
      case "COMPLETED":
        return "bg-green-200 text-green-800";
      default:
        return "bg-gray-200 text-gray-800";
    }
  };

  // Function to determine the priority badge color
  const getPriorityBadgeColor = (priority: Task["priority"]): string => {
    switch (priority) {
      case "LOW":
        return "bg-green-100 text-green-800";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800";
      case "HIGH":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none z-50">
          <svg
            className="w-4 h-4 text-gray-500"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 20"
          >
            <path
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"
            />
          </svg>
        </div>
        <input
          type="search"
          className="block w-full p-4 pl-10 text-sm border text-base-content border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          placeholder="Search tasks..."
          value={searchQuery}
          onChange={handleSearchChange}
        />
      </div>

      {searchQuery && (
        <div className="mt-2 border border-gray-300 rounded-lg shadow-sm max-h-80 overflow-y-auto absolute z-10 bg-base-100">
          {filteredTasks.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {filteredTasks.map((task) => (
                <li
                  key={task.id}
                  className="px-4 py-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => onTaskSelect(task)}
                >
                  <div className="flex flex-col">
                    <div className="font-medium">
                      {highlightMatch(task.title, searchQuery)}
                    </div>

                    {task.description && (
                      <div className="text-sm text-accent-content mt-1 truncate">
                        {task.description}
                      </div>
                    )}

                    <div className="flex items-center gap-2 mt-2">
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${getStatusBadgeColor(
                          task.status
                        )}`}
                      >
                        {task.status}
                      </span>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${getPriorityBadgeColor(
                          task.priority
                        )}`}
                      >
                        {task.priority}
                      </span>
                      {task.dueDate && (
                        <span className="text-xs text-base-content">
                          Due: {new Date(task.dueDate).toLocaleDateString()}
                        </span>
                      )}
                      {task.subtasks.length > 0 && (
                        <span className="text-xs">
                          Subtasks: {task.subtasks.length}
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-4 py-3 text-sm text-accent">
              No matching tasks found
            </div>
          )}
        </div>
      )}
    </div>
  );
};
