import React, { useState } from "react";
import apiClient from "@/api/axiosClient";
import { isAxiosError } from "axios";
import ConflictResolverModal from "./ConflictResolverModal";
import SuggestionSelectionModal from "./SuggestionSelectionModal";

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
    dueDateTime?: string | null;
    windowStart?: string | null;  // CRITICAL FIX: Store time window constraints
    windowEnd?: string | null;    // CRITICAL FIX: Store time window constraints
  } | null>(null);
  const [lastQuery, setLastQuery] = useState<string>("");

  // paging for suggestions (1-based)
  const [page, setPage] = useState(1);
  const [hasMorePages, setHasMorePages] = useState(true);

  // Conflict resolution modal state
  const [showConflictModal, setShowConflictModal] = useState(false);
  
  // Track the last strategy used for pagination
  const [lastStrategy, setLastStrategy] = useState<"day" | "week" | "month" | "auto">("auto");

  const toast = (msg: string) => alert(msg);

  const resetState = () => {
    console.log("[RESET STATE] ============================================");
    console.log("[RESET STATE] resetState() called!");
    console.log("[RESET STATE] Current parsedMeta before reset:", parsedMeta);
    console.log("[RESET STATE] Stack trace:", new Error().stack);
    console.log("[RESET STATE] ============================================");
    
    setInputText("");
    setSuggestions([]);
    setParsedMeta(null);
    setShowModal(false);
    setPage(1); // <-- important: reset paging
    setHasMorePages(true); // Reset hasMorePages
    setLastStrategy("auto"); // Reset strategy
    setShowConflictModal(false); // Reset conflict modal state
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
      const data: {
        status: "complete" | "partial";
        parsed: {
          title?: string;
          task_type?: "Meeting" | "Training" | "Studies";
          dueDateTime?: string | null;
          durationMinutes?: number | null;
          priority?: "LOW" | "MEDIUM" | "HIGH";
        };
        suggestions?: Suggestion[];
        shouldCreateDirectly?: boolean;
        task?: any;
        case?: string;
      } = res.data;

      if (data.status === "complete" || data.shouldCreateDirectly) {
        // Parse metadata for potential conflict resolution
        const parsed = data.parsed || {};
        setParsedMeta({
          title: parsed.title || "New task",
          task_type: parsed.task_type || "Meeting",
          priority: (parsed.priority as any) || "MEDIUM",
          durationMinutes: parsed.durationMinutes ?? null,
          dueDateTime: parsed.dueDateTime ?? null,
          windowStart: (parsed as any).windowStart ?? null,
          windowEnd: (parsed as any).windowEnd ?? null,
        });

        // CASE 4: Backend already created task with default duration
        if (data.shouldCreateDirectly && data.task) {
          console.log("[CASE 4 DEBUG] ============================================");
          console.log("[CASE 4 DEBUG] Task created by backend (Rule 4)");
          console.log("[CASE 4 DEBUG] Task ID:", data.task.id);
          console.log("[CASE 4 DEBUG] Task Title:", data.task.title);
          console.log("[CASE 4 DEBUG] Scheduled Start:", data.task.scheduledStart);
          console.log("[CASE 4 DEBUG] Scheduled End:", data.task.scheduledEnd);
          console.log("[CASE 4 DEBUG] Due Date:", data.task.dueDate);
          console.log("[CASE 4 DEBUG] Full task object:", data.task);
          console.log("[CASE 4 DEBUG] Case identifier:", data.case);
          console.log("[CASE 4 DEBUG] onTaskCreated callback exists:", !!onTaskCreated);
          console.log("[CASE 4 DEBUG] About to call onTaskCreated to refresh parent...");
          
          resetState();
          
          if (onTaskCreated) {
            console.log("[CASE 4 DEBUG] Calling onTaskCreated()...");
            await onTaskCreated();
            console.log("[CASE 4 DEBUG] ✅ onTaskCreated() completed");
            
            // Silent task creation - log details but no popup
            if (data.task.scheduledStart) {
              const taskDate = new Date(data.task.scheduledStart);
              const taskMonth = taskDate.toLocaleString('default', { month: 'long', year: 'numeric' });
              const taskDay = taskDate.getDate();
              
              console.log(`[CASE 4 DEBUG] ✅ Task created successfully for ${taskMonth} ${taskDay}`);
              console.log("[CASE 4 DEBUG] Task will appear on calendar automatically");
            }
          } else {
            console.error("[CASE 4 DEBUG] ❌ onTaskCreated callback is undefined!");
          }
          
          console.log("[CASE 4 DEBUG] ============================================");
          return;
        }

        // CASE 2.A: All fields present, attempt creation
        try {
          await apiClient.post("/ai/createFromText", { text });
          resetState();
          await onTaskCreated?.();
          return;
        } catch (createErr: any) {
          // Handle 409 Conflict - time slot already occupied
          if (isAxiosError(createErr) && createErr.response?.status === 409) {
            console.log("Conflict detected, showing resolution modal");
            
            // CRITICAL FIX: Extract task data from 409 response for suggestions
            const conflictData = createErr.response?.data;
            console.log("Conflict data from 409:", conflictData);
            
            // Update parsedMeta with conflict data so suggest endpoint gets correct date
            setParsedMeta({
              title: conflictData.title || parsed.title || "New task",
              task_type: conflictData.task_type || parsed.task_type || "Meeting",
              priority: conflictData.priority || parsed.priority || "MEDIUM",
              durationMinutes: conflictData.durationMinutes ?? parsed.durationMinutes ?? null,
              dueDateTime: conflictData.scheduledStart || conflictData.dueDate || parsed.dueDateTime || null,
              windowStart: (parsed as any).windowStart ?? null,
              windowEnd: (parsed as any).windowEnd ?? null,
            });
            
            setShowConflictModal(true);
            setIsLoading(false);
            return;
          }
          // Re-throw other errors to be handled by outer catch
          throw createErr;
        }
      }

      const parsed = data.parsed || {};
      const extractedDate = parsed.dueDateTime ?? null;
      
      console.log("[NLP PARSE] ============================================");
      console.log("[NLP PARSE] Parsed data from backend:", parsed);
      console.log("[NLP PARSE] Extracted date:", extractedDate);
      console.log("[NLP PARSE] ============================================");
      
      const newParsedMeta = {
        title: parsed.title || "New task",
        task_type: parsed.task_type || "Meeting",
        priority: (parsed.priority as any) || "MEDIUM",
        durationMinutes: parsed.durationMinutes ?? null,
        dueDateTime: extractedDate,
        windowStart: (parsed as any).windowStart ?? null,  // CRITICAL FIX: Preserve window constraints
        windowEnd: (parsed as any).windowEnd ?? null,      // CRITICAL FIX: Preserve window constraints
      };
      
      console.log("[NLP PARSE] Setting parsedMeta to:", newParsedMeta);
      console.log("[WINDOW CONSTRAINT] windowStart:", newParsedMeta.windowStart);
      console.log("[WINDOW CONSTRAINT] windowEnd:", newParsedMeta.windowEnd);
      setParsedMeta(newParsedMeta);
      
      // If we have a date but no exact time (partial status), fetch date-locked suggestions
      // CRITICAL: Use 'day' strategy and pass scheduledStart to lock to the extracted date
      if (extractedDate && data.status === "partial") {
        console.log("[NLP DATE LOCK] Date provided, fetching suggestions for:", extractedDate);
        setLastStrategy("day"); // Lock to 'day' strategy
        
        try {
          const res = await apiClient.post("/ai/suggest", {
            durationMinutes: parsed.durationMinutes || undefined, // Backend uses user preference if not provided
            task_type: parsed.task_type || "Meeting",
            strategy: "day", // Force 'day' strategy for date locking
            referenceDate: new Date(extractedDate).toISOString(),
            scheduledStart: new Date(extractedDate).toISOString(), // CRITICAL: Lock to this date
            page: 1,
            pageSize: 3,
          });
          
          const suggestData = res.data;
          setSuggestions(suggestData.suggestions || []);
          setPage(1);
          setShowModal(true);
        } catch (suggestErr) {
          console.error("Failed to fetch date-locked suggestions:", suggestErr);
          // Fallback to original suggestions from parseTask
          setSuggestions(data.suggestions || []);
          setPage(1);
          setShowModal(true);
        }
      } else {
        // No date provided, use original suggestions
        setSuggestions(data.suggestions || []);
        setPage(1);
        setShowModal(true);
      }
    } catch (err: any) {
      if (isAxiosError(err)) {
        // CRITICAL FIX: Handle 409 from parseTask (overlap detected during parse)
        if (err.response?.status === 409) {
          console.log("Conflict detected in parseTask, showing resolution modal");
          
          const conflictData = err.response?.data;
          console.log("Conflict data from parseTask 409:", conflictData);
          
          // Extract parsed data from 409 response
          const parsed = conflictData.parsed || {};
          setParsedMeta({
            title: conflictData.title || parsed.title || "New task",
            task_type: conflictData.task_type || parsed.task_type || "Meeting",
            priority: conflictData.priority || parsed.priority || "MEDIUM",
            durationMinutes: conflictData.durationMinutes ?? parsed.durationMinutes ?? null,
            dueDateTime: conflictData.scheduledStart || conflictData.dueDate || parsed.dueDateTime || null,
            windowStart: (parsed as any).windowStart ?? null,
            windowEnd: (parsed as any).windowEnd ?? null,
          });
          
          setShowConflictModal(true);
          setIsLoading(false);
          return;
        }
        
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

  // Navigate to specific page of suggestions
  const fetchSuggestionsPage = async (targetPage: number, preservedConstraints?: {scheduledStart?: string; strategy?: string; durationMinutes?: number}) => {
    console.log("[PAGINATION] ============================================");
    console.log("[PAGINATION] fetchSuggestionsPage called");
    console.log("[PAGINATION] Target page:", targetPage);
    console.log("[PAGINATION] Preserved constraints from modal:", preservedConstraints);
    console.log("[PAGINATION] parsedMeta exists:", !!parsedMeta);
    console.log("[PAGINATION] Full parsedMeta:", parsedMeta);
    
    // CRITICAL: If we have preserved constraints from modal, use them
    // Otherwise fall back to parsedMeta
    if (!preservedConstraints && !parsedMeta) {
      console.error("[PAGINATION] ❌ CRITICAL ERROR: No constraints OR parsedMeta available");
      console.error("[PAGINATION] ❌ Cannot paginate without constraints");
      return;
    }
    
    if (targetPage < 1) {
      console.error("[PAGINATION] Invalid page number:", targetPage);
      return;
    }
    
    // CRITICAL: Triple-fallback data binding for date constraint
    // Priority: 1) preservedConstraints (from modal), 2) parsedMeta (from NLP), 3) null
    const lockedDate = preservedConstraints?.scheduledStart || parsedMeta?.dueDateTime || null;
    const lockedDuration = preservedConstraints?.durationMinutes || parsedMeta?.durationMinutes || null;
    const lockedTaskType = parsedMeta?.task_type || "Meeting";
    
    console.log("[PAGINATION STATE CHECK] ============================================");
    console.log("[PAGINATION STATE CHECK] Data Source Priority:");
    console.log("[PAGINATION STATE CHECK]   1. preservedConstraints.scheduledStart:", preservedConstraints?.scheduledStart);
    console.log("[PAGINATION STATE CHECK]   2. parsedMeta.dueDateTime:", parsedMeta?.dueDateTime);
    console.log("[PAGINATION STATE CHECK] RESOLVED VALUES:");
    console.log("[PAGINATION STATE CHECK]   - Locked Date:", lockedDate);
    console.log("[PAGINATION STATE CHECK]   - Locked Duration:", lockedDuration);
    console.log("[PAGINATION STATE CHECK]   - Task Type:", lockedTaskType);
    console.log("[PAGINATION STATE CHECK]   - Strategy:", lastStrategy);
    
    if (lastStrategy === "day" && !lockedDate) {
      console.error("[PAGINATION STATE CHECK] ❌ CRITICAL: Strategy is 'day' but no date in parsedMeta!");
      console.error("[PAGINATION STATE CHECK] ❌ Cannot maintain date lock without date!");
    }
    console.log("[PAGINATION STATE CHECK] ============================================");
    
    setIsLoading(true);
    try {
      // Use the task's dueDateTime for date context
      let referenceDate = new Date().toISOString();
      if (lockedDate) {
        referenceDate = new Date(lockedDate).toISOString();
        console.log("[PAGINATION] ✅ Using locked date:", referenceDate);
      }
      
      // CRITICAL FIX: Extract window constraints from parsedMeta
      const windowStart = parsedMeta?.windowStart || null;
      const windowEnd = parsedMeta?.windowEnd || null;
      
      // CRITICAL: Use local variables to ensure constraints are preserved
      const requestPayload = {
        durationMinutes: lockedDuration || undefined, // Backend uses user preference if not provided
        task_type: lockedTaskType || parsedMeta?.task_type || "Meeting",
        strategy: preservedConstraints?.strategy || lastStrategy,
        referenceDate: referenceDate,
        page: targetPage,
        pageSize: 3,
        dueDate: lockedDate || null,
        scheduledStart: lockedDate || null,  // CRITICAL: Must be present for date-locked searches
        windowStart: windowStart,  // CRITICAL FIX: Preserve window constraints for "next week" etc.
        windowEnd: windowEnd,      // CRITICAL FIX: Preserve window constraints for "next week" etc.
      };
      
      console.log("[PAGINATION] ============================================");
      console.log("[PAGINATION] Request payload for page", targetPage);
      console.log("[PAGINATION]   - scheduledStart:", requestPayload.scheduledStart);
      console.log("[PAGINATION]   - windowStart:", requestPayload.windowStart);
      console.log("[PAGINATION]   - windowEnd:", requestPayload.windowEnd);
      console.log("[PAGINATION]   - strategy:", requestPayload.strategy);
      console.log("[PAGINATION]   - referenceDate:", requestPayload.referenceDate);
      console.log("[PAGINATION]   - page:", requestPayload.page);
      
      if (windowStart && windowEnd) {
        console.log("[PAGINATION] ✅ Sending window constraint:", { windowStart, windowEnd });
      } else {
        console.log("[PAGINATION] ⚪ No window constraint (flexible date range)");
      }
      
      // CRITICAL VALIDATION: Ensure scheduledStart is present for date-locked searches
      if (lastStrategy === "day" && !requestPayload.scheduledStart) {
        console.error("[PAGINATION] ⚠️  WARNING: Strategy is 'day' but scheduledStart is null!");
        console.error("[PAGINATION] ⚠️  This will cause the backend to lose the date lock!");
        console.error("[PAGINATION] ⚠️  parsedMeta.dueDateTime:", parsedMeta?.dueDateTime);
        console.error("[PAGINATION] ⚠️  preservedConstraints:", preservedConstraints);
      } else if (lastStrategy === "day" && requestPayload.scheduledStart) {
        console.log("[PAGINATION] ✅ Date-locked request: scheduledStart is present");
      }
      
      console.log("[PAGINATION] ============================================");
      
      // CRITICAL DEBUG: Show EXACT payload that will be sent to backend
      console.log("[PAGINATION DEBUG] ============================================");
      console.log("[PAGINATION DEBUG] About to send axios.post to /ai/suggest");
      console.log("[PAGINATION DEBUG] Sending date to backend:", requestPayload.scheduledStart);
      console.log("[PAGINATION DEBUG] Full payload object:", requestPayload);
      console.log("[PAGINATION DEBUG] Serialized JSON:", JSON.stringify(requestPayload, null, 2));
      console.log("[PAGINATION DEBUG] scheduledStart type:", typeof requestPayload.scheduledStart);
      console.log("[PAGINATION DEBUG] scheduledStart value:", requestPayload.scheduledStart);
      console.log("[PAGINATION DEBUG] strategy:", requestPayload.strategy);
      console.log("[PAGINATION DEBUG] page:", requestPayload.page);
      
      if (requestPayload.scheduledStart) {
        console.log("[PAGINATION DEBUG] ✅ Date present in request - backend will maintain date lock");
      } else {
        console.warn("[PAGINATION DEBUG] ⚠️ No date in request - backend will search all dates");
      }
      console.log("[PAGINATION DEBUG] ============================================");
      
      // Call suggest endpoint with page parameter
      const res = await apiClient.post("/ai/suggest", requestPayload);
      
      const data = res.data;
      
      console.log("[DEBUG UI] API response data:", data);
      console.log("[DEBUG UI] New suggestions received:", data.suggestions);
      console.log("[DEBUG UI] Number of suggestions:", data.suggestions?.length);
      
      if (Array.isArray(data?.suggestions) && data.suggestions.length) {
        console.log("[PAGINATION] Received", data.suggestions.length, "suggestions for page", targetPage);
        
        // Force new array reference to trigger React re-render
        setSuggestions([...data.suggestions]);
        setPage(targetPage);
        setHasMorePages(true); // Reset hasMorePages when we get results
        
        console.log("[DEBUG UI] State updated with new suggestions");
        console.log("[DEBUG UI] New page state:", targetPage);
      } else {
        // No more results - disable Next button, stay on current page
        console.log("[PAGINATION] No more suggestions available - disabling Next button");
        setHasMorePages(false);
      }
    } catch (e: any) {
      console.error("[PAGINATION] Error fetching suggestions:", e);
      
      // Handle backend validation error for missing scheduledStart
      if (isAxiosError(e) && e.response?.status === 400) {
        const errorData = e.response?.data;
        if (errorData?.error === "PAGINATION_CONSTRAINT_VIOLATION") {
          console.error("[PAGINATION] ❌❌❌ BACKEND VALIDATION ERROR ❌❌❌");
          console.error("[PAGINATION] Backend rejected pagination request:");
          console.error("[PAGINATION] Message:", errorData.message);
          console.error("[PAGINATION] Details:", errorData.details);
          toast(`Pagination Error: ${errorData.message}\n\nHint: ${errorData.details?.hint}`);
          
          // Close modal since we can't paginate without constraints
          setShowModal(false);
          resetState();
          return;
        }
      }
      
      toast("Failed to fetch suggestions");
    } finally {
      setIsLoading(false);
    }
  };

  // Next page handler - now accepts preserved constraints from modal
  const refreshSuggestions = async (preservedConstraints?: {scheduledStart?: string; strategy?: string; durationMinutes?: number}) => {
    console.log("[REFRESH SUGGESTIONS] ============================================");
    console.log("[REFRESH SUGGESTIONS] Called from modal Next button");
    console.log("[REFRESH SUGGESTIONS] Current page:", page);
    console.log("[REFRESH SUGGESTIONS] Next page will be:", page + 1);
    console.log("[REFRESH SUGGESTIONS] ============================================");
    console.log("[REFRESH SUGGESTIONS] PRESERVED CONSTRAINTS FROM MODAL:");
    console.log("[REFRESH SUGGESTIONS]   - scheduledStart:", preservedConstraints?.scheduledStart);
    console.log("[REFRESH SUGGESTIONS]   - strategy:", preservedConstraints?.strategy);
    console.log("[REFRESH SUGGESTIONS]   - durationMinutes:", preservedConstraints?.durationMinutes);
    console.log("[REFRESH SUGGESTIONS] ============================================");
    console.log("[REFRESH SUGGESTIONS] Current parsedMeta:", parsedMeta);
    console.log("[REFRESH SUGGESTIONS] parsedMeta.dueDateTime:", parsedMeta?.dueDateTime);
    console.log("[REFRESH SUGGESTIONS] lastStrategy:", lastStrategy);
    
    // CRITICAL: Use preserved constraints if provided, otherwise fall back to parsedMeta
    const dateToUse = preservedConstraints?.scheduledStart || parsedMeta?.dueDateTime;
    const durationToUse = preservedConstraints?.durationMinutes || parsedMeta?.durationMinutes;
    const strategyToUse = preservedConstraints?.strategy || lastStrategy;
    
    console.log("[REFRESH SUGGESTIONS] ============================================");
    console.log("[REFRESH SUGGESTIONS] RESOLVED VALUES FOR PAGINATION:");
    console.log("[REFRESH SUGGESTIONS]   - Date to use:", dateToUse);
    console.log("[REFRESH SUGGESTIONS]   - Duration to use:", durationToUse);
    console.log("[REFRESH SUGGESTIONS]   - Strategy to use:", strategyToUse);
    
    if (preservedConstraints?.scheduledStart) {
      console.log("[REFRESH SUGGESTIONS] ✅ Using MODAL'S preserved date:", preservedConstraints.scheduledStart);
    } else if (parsedMeta?.dueDateTime) {
      console.log("[REFRESH SUGGESTIONS] ⚠️ Using parsedMeta date (no modal constraints):", parsedMeta.dueDateTime);
    } else {
      console.error("[REFRESH SUGGESTIONS] ❌ NO DATE AVAILABLE - pagination will fail!");
    }
    
    console.log("[REFRESH SUGGESTIONS] About to call fetchSuggestionsPage...");
    console.log("[REFRESH SUGGESTIONS] ============================================");
    await fetchSuggestionsPage(page + 1, preservedConstraints);
  };

  // Previous page handler
  const goToPreviousPage = async () => {
    if (page > 1) {
      setHasMorePages(true); // Reset when going back (might have more pages from current position)
      await fetchSuggestionsPage(page - 1);
    }
  };

  // Back to strategy selection
  const backToStrategySelection = () => {
    console.log("[UI] User requested back to strategy selection");
    setShowModal(false);
    setShowConflictModal(true);
    setPage(1); // Reset page when going back
    setHasMorePages(true); // Reset hasMorePages
  };

  // Handle conflict resolution strategy selection
  const handleConflictResolve = async (strategy: "day" | "week" | "month" | "auto") => {
    if (!parsedMeta) return;

    setIsLoading(true);
    setShowConflictModal(false);
    
    // Store strategy for pagination
    setLastStrategy(strategy);

    try {
      // CRITICAL FIX: Use the task's dueDateTime, not today's date!
      let referenceDate = new Date().toISOString();
      if (parsedMeta.dueDateTime) {
        referenceDate = new Date(parsedMeta.dueDateTime).toISOString();
        console.log("[NLP CONFLICT] Using task date:", referenceDate);
      } else {
        console.log("[NLP CONFLICT] No dueDateTime, using current date:", referenceDate);
      }

      const res = await apiClient.post("/ai/suggest", {
        durationMinutes: parsedMeta.durationMinutes || undefined, // Backend uses user preference if not provided
        task_type: parsedMeta.task_type || "Meeting",
        strategy: strategy,
        referenceDate: referenceDate,
        page: 1,  // Start at page 1
        pageSize: 3,  // UX: Show top 3 scored suggestions per page
        dueDate: parsedMeta.dueDateTime || null,
        scheduledStart: parsedMeta.dueDateTime || null, // CRITICAL: Pass date to lock suggestions
      });

      const data = res.data;
      if (Array.isArray(data?.suggestions) && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
        setPage(1);
        setHasMorePages(true);
        setShowModal(true); // Show the existing suggestion modal
      } else {
        toast("No available time slots found for the selected strategy.");
      }
    } catch (err: any) {
      console.error("Failed to fetch conflict resolution suggestions:", err);
      toast("Failed to fetch alternative time slots. Please try again.");
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

        {/* Conflict Resolution Modal */}
        <ConflictResolverModal
          isOpen={showConflictModal}
          onClose={() => setShowConflictModal(false)}
          onResolve={handleConflictResolve}
        />

        {/* Suggestions modal */}
        <SuggestionSelectionModal
          isOpen={showModal}
          onClose={() => {
            console.log("[MODAL CLOSE] User closing modal");
            setShowModal(false);
          }}
          suggestions={suggestions}
          onSelect={handlePickSuggestion}
          isLoading={isLoading}
          metadata={parsedMeta}
          onRefresh={(preservedConstraints) => {
            console.log("[MODAL REFRESH] ============================================");
            console.log("[MODAL REFRESH] Modal's onRefresh callback triggered");
            console.log("[MODAL REFRESH] RECEIVED CONSTRAINTS FROM MODAL:");
            console.log("[MODAL REFRESH]   - scheduledStart:", preservedConstraints?.scheduledStart);
            console.log("[MODAL REFRESH]   - strategy:", preservedConstraints?.strategy);
            console.log("[MODAL REFRESH]   - durationMinutes:", preservedConstraints?.durationMinutes);
            console.log("[MODAL REFRESH] ============================================");
            console.log("[MODAL REFRESH] Current parsedMeta:", parsedMeta);
            console.log("[MODAL REFRESH] parsedMeta.dueDateTime:", parsedMeta?.dueDateTime);
            console.log("[MODAL REFRESH] Current page:", page);
            
            if (preservedConstraints?.scheduledStart) {
              console.log("[MODAL REFRESH] ✅ Modal passed date constraint:", preservedConstraints.scheduledStart);
              console.log("[MODAL REFRESH] ✅ This will be used for pagination!");
            } else {
              console.error("[MODAL REFRESH] ❌ No date constraint from modal!");
            }
            
            console.log("[MODAL REFRESH] About to call refreshSuggestions with constraints...");
            console.log("[MODAL REFRESH] ============================================");
            refreshSuggestions(preservedConstraints);
          }}
          onPrevious={goToPreviousPage}
          onBackToOptions={backToStrategySelection}
          page={page}
          hasMorePages={hasMorePages}
          isConflict={false} // This is missing info flow, not conflict
          initialConstraints={{
            lockedDate: parsedMeta?.dueDateTime || null,
            lockedDuration: parsedMeta?.durationMinutes || null,
            strategy: lastStrategy || "auto",
            isConflict: false,
          }}
        />
      </div>

      {/* optional error area */}
      {/* {errorMessage && <div className="mt-2 text-error text-sm">{errorMessage}</div>} */}
    </div>
  );
};

export default NaturalLanguageTaskInput;
