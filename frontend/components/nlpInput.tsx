import React, { useState } from 'react';
import { Task } from './tasksTypes';
import { createNlpTask } from '@/utils/taskUtils';

interface NaturalLanguageInputProps {
  onTaskCreated: (task: Task) => void;
}

const NaturalLanguageTaskInput: React.FC<NaturalLanguageInputProps> = ({ onTaskCreated }) => {
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();


    if (!inputText.trim()) return;

    setIsLoading(true);
    setErrorMessage("");

    try {

      const response = createNlpTask(inputText)

      if (!response) {
        throw new Error('Failed to create task');

      }

      const newTask = await response;
      onTaskCreated(newTask);
      setInputText("");
    } catch (error) {
      console.error('Error creating task:', error);
      setErrorMessage(error instanceof Error ? error.message : `An unknown error occurred`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="w-full mb-6">
      <div className="bg-base-200 rounded-lg shadow-md p-4">
        <h3 className="text-lg font-medium mb-2">Add Task Quickly</h3>
        <p className="text-sm mb-3 text-base-content/80">
          Type your task in natural language. For example:
          &ldquo;High priority meeting with John about project tomorrow at 3pm&rdquo; or
          &ldquo;Finish report by Friday&rdquo;
        </p>

        <form onSubmit={handleSubmit} className="relative">
          <textarea
            className="w-full p-3 bg-base-100 rounded-md border border-base-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent min-h-16 pr-24"
            placeholder="Describe your task..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            data-testid="nlp-input"
          />

          <button
            type="submit"
            disabled={isLoading || !inputText.trim()}
            className={`absolute right-2 bottom-2 px-4 py-2 rounded-md ${isLoading || !inputText.trim()
              ? 'bg-base-300 text-base-content/50 cursor-not-allowed'
              : 'bg-primary text-primary-content hover:bg-primary-focus'
              } transition-colors`}
            data-testid="nlp-submit"
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing
              </span>
            ) : (
              'Add Task'
            )}
          </button>
        </form>

        {errorMessage && (
          <div className="mt-2 text-error text-sm">
            {errorMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default NaturalLanguageTaskInput;
