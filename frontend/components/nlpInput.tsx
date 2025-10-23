import React, { useState } from "react";
import apiClient from "@/api/axiosClient";
import { isAxiosError } from "axios";

type Suggestion = {
  scheduledStart: string;
  scheduledEnd: string;
  score?: number;
};

interface NaturalLanguageTaskInputProps {
  // Parent should pass a function that reloads the tasks list (e.g., getTasks)
  onTaskCreated: () => Promise<void> | void;
}

const NaturalLanguageTaskInput: React.FC<NaturalLanguageTaskInputProps> = ({ onTaskCreated }) => {
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Suggestions modal state
  const [showModal, setShowModal] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [parsedMeta, setParsedMeta] = useState<{
    title?: string;
    task_type?: "Meeting" | "Training" | "Studies";
    priority?: "LOW" | "MEDIUM" | "HIGH";
    durationMinutes?: number | null;
  } | null>(null);
  const [lastQuery, setLastQuery] = useState<string>("");

  // paging for suggestions (1-based)
  const [page, setPage] = useState(1);

  const toast = (msg: string) => alert(msg);

  const resetState = () => {
    setInputText("");
    setSuggestions([]);
    setParsedMeta(null);
    setShowModal(false);
    setPage(1); // <-- important: reset paging
  };

  // Parse text → if complete create immediately; if partial show suggestions modal
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text) return;

    setIsLoading(true);
    try {
      setLastQuery(text);
      const res = await apiClient.post("/ai/parseTask", { text });
      const data = res.data as {
        status: "complete" | "partial";
        parsed: {
          title?: string;
          task_type?: "Meeting" | "Training" | "Studies";
          dueDateTime?: string | null;
          durationMinutes?: number | null;
          priority?: "LOW" | "MEDIUM" | "HIGH";
        };
        suggestions?: Suggestion[];
      };

      if (data.status === "complete") {
        await apiClient.post("/ai/createFromText", { text });
        resetState();
        await onTaskCreated?.();
        return;
      }

      const parsed = data.parsed || {};
      setParsedMeta({
        title: parsed.title || "New task",
        task_type: parsed.task_type || "Meeting",
        priority: (parsed.priority as any) || "MEDIUM",
        durationMinutes: parsed.durationMinutes ?? null,
      });
      setSuggestions(data.suggestions || []);
      setPage(1);            // <-- start paging for this query from 1
      setShowModal(true);
    } catch (err: any) {
      if (isAxiosError(err)) {
        console.error("parseTask failed", {
          status: err.response?.status,
          data: err.response?.data,
          message: err.message,
        });
        const msg =
          err.response?.data?.message ||
          err.response?.data?.error ||
          `Request failed${err.response?.status ? ` (${err.response.status})` : ""}`;
        toast(msg);
      } else {
        console.error("parseTask failed (non-axios)", err);
        toast("Failed to process text");
      }

      // Some backends return partial results inside an error payload
      const result = err?.response?.data?.result;
      if (result?.status === "partial" && Array.isArray(result?.suggestions)) {
        const parsed = result.parsed || {};
        setParsedMeta({
          title: parsed.title || "New task",
          task_type: parsed.task_type || "Meeting",
          priority: (parsed.priority as any) || "MEDIUM",
          durationMinutes: parsed.durationMinutes ?? null,
        });
        setSuggestions(result.suggestions);
        setPage(1);        // <-- reset page for this result set as well
        setShowModal(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Create task from chosen suggestion
  const handlePickSuggestion = async (s: Suggestion) => {
    if (!parsedMeta) return;
    try {
      await apiClient.post("/ai/createFromSuggestion", {
        title: parsedMeta.title || "New task",
        task_type: parsedMeta.task_type || "Meeting",
        priority: (parsedMeta.priority || "MEDIUM").toUpperCase(),
        durationMinutes: parsedMeta.durationMinutes ?? undefined,
        scheduledStart: s.scheduledStart,
        scheduledEnd: s.scheduledEnd,
      });

      resetState();
      await onTaskCreated?.();
    } catch (err: any) {
      if (isAxiosError(err)) {
        console.error("createFromSuggestion failed", {
          status: err.response?.status,
          data: err.response?.data,
          message: err.message,
        });
        const msg =
          err.response?.data?.message ||
          err.response?.data?.error ||
          `Request failed${err.response?.status ? ` (${err.response.status})` : ""}`;
        toast(msg);
      } else {
        console.error("createFromSuggestion failed (non-axios)", err);
        toast("Failed to create task from suggestion");
      }
    }
  };

  // Refresh suggestions list (next page)
  const refreshSuggestions = async () => {
    if (!lastQuery) return;
    setIsLoading(true);
    try {
      const nextPage = page + 1;
      const res = await apiClient.post(`/ai/parseTask?page=${nextPage}`, { text: lastQuery });
      const data = res.data;
      if (Array.isArray(data?.suggestions) && data.suggestions.length) {
        setSuggestions(data.suggestions);
        setPage(nextPage);
      } else {
        toast("No more suggestions");
      }
    } catch (e) {
      console.error("refresh suggestions error", e);
      toast("Failed to refresh suggestions");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit(e as unknown as React.FormEvent);
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
            className={`absolute right-2 bottom-2 px-4 py-2 rounded-md ${
              isLoading || !inputText.trim()
                ? "bg-base-300 text-base-content/50 cursor-not-allowed"
                : "bg-primary text-primary-content hover:bg-primary-focus"
            } transition-colors`}
            data-testid="nlp-submit"
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Processing
              </span>
            ) : (
              "Add Task"
            )}
          </button>
        </form>

        {/* Suggestions modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-base-100 rounded-lg shadow-xl w-full max-w-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold">Choose a time slot</h3>
                <button className="btn btn-ghost btn-sm" onClick={() => setShowModal(false)}>
                  ✕
                </button>
              </div>

              {parsedMeta && (
                <div className="mb-4 text-sm opacity-80">
                  <div><b>Title:</b> {parsedMeta.title}</div>
                  <div><b>Type:</b> {parsedMeta.task_type}</div>
                  <div><b>Priority:</b> {parsedMeta.priority}</div>
                  {parsedMeta.durationMinutes ? (
                    <div><b>Duration:</b> {parsedMeta.durationMinutes} minutes</div>
                  ) : (
                    <div><b>Duration:</b> from suggested start/end</div>
                  )}
                </div>
              )}

              <div className="space-y-3">
                {suggestions.map((s, idx) => (
                  <div key={idx} className="card bg-base-200">
                    <div className="card-body flex-row items-center justify-between">
                      <div className="text-sm">
                        <div><b>Start:</b> {new Date(s.scheduledStart).toLocaleString()}</div>
                        <div><b>End:</b> {new Date(s.scheduledEnd).toLocaleString()}</div>
                        {typeof s.score === "number" && (
                          <div><b>Score:</b> {s.score}</div>
                        )}
                      </div>
                      <button className="btn btn-success btn-sm" onClick={() => handlePickSuggestion(s)}>
                        Choose
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex gap-2 justify-end">
                <button className="btn btn-ghost" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button
                  className={`btn ${isLoading ? "loading" : ""}`}
                  onClick={refreshSuggestions}
                  disabled={isLoading}
                >
                  {isLoading ? "Loading..." : "Refresh suggestions"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* optional error area */}
      {/* {errorMessage && <div className="mt-2 text-error text-sm">{errorMessage}</div>} */}
    </div>
  );
};

export default NaturalLanguageTaskInput;
