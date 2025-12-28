import React, { useState, useEffect } from "react";
import { DateTimeRangeBadges } from "./DateBadges";
import apiClient from "../api/axiosClient";

type Suggestion = {
  scheduledStart: string;
  scheduledEnd: string;
  score?: number;
  exceedsWorkHours?: boolean;
};

interface TaskMetadata {
  title?: string;
  task_type?: string;
  priority?: string;
  durationMinutes?: number | null;
}

interface ActiveConstraints {
  lockedDate?: string | null; // ISO date string for date-locked searches
  lockedTime?: string | null; // HH:MM format for time-locked searches
  lockedDuration?: number | null; // Duration in minutes
  strategy?: string; // "day", "week", "month", "auto"
  isConflict: boolean; // True for conflict resolution, false for NLP completion
}

interface SuggestionSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  suggestions: Suggestion[];
  onSelect: (suggestion: Suggestion) => void;
  isLoading?: boolean;
  metadata?: TaskMetadata | null;
  onRefresh?: (preservedConstraints?: {scheduledStart?: string; strategy?: string; durationMinutes?: number}) => void;
  page?: number;
  onPrevious?: () => void;
  onBackToOptions?: () => void;
  hasMorePages?: boolean;
  isConflict?: boolean; // If true, show "Change Slots" button and "Resolve Conflict" title
  // NEW: Initial constraints for internal pagination
  initialConstraints?: Partial<ActiveConstraints>;
}

const SuggestionSelectionModal: React.FC<SuggestionSelectionModalProps> = ({
  isOpen,
  onClose,
  suggestions,
  onSelect,
  isLoading = false,
  metadata = null,
  onRefresh,
  page = 1,
  onPrevious,
  onBackToOptions,
  hasMorePages = true,
  isConflict = false, // Default to false (missing info flow)
  initialConstraints,
}) => {
  // Internal state for managing constraints across pagination
  const [activeConstraints, setActiveConstraints] = useState<ActiveConstraints>({
    lockedDate: null,
    lockedTime: null,
    lockedDuration: null,
    strategy: "auto",
    isConflict: isConflict,
  });
  
  // Initialize constraints from props when modal opens
  useEffect(() => {
    if (isOpen && initialConstraints) {
      console.log("[MODAL CONSTRAINTS] Initializing from props:", initialConstraints);
      setActiveConstraints(prev => ({
        ...prev,
        ...initialConstraints,
        isConflict: isConflict, // Always use prop value
      }));
    }
  }, [isOpen, initialConstraints, isConflict]);
  // DEBUG: Log when modal renders
  console.log("[MODAL DEBUG] Rendering SuggestionSelectionModal", {
    isOpen,
    suggestionsCount: suggestions.length,
    isLoading,
    hasOnSelect: typeof onSelect === 'function',
    hasOnRefresh: typeof onRefresh === 'function',
    page,
    metadata,
    activeConstraints,
    firstSuggestion: suggestions[0]?.scheduledStart,
    lastSuggestion: suggestions[suggestions.length - 1]?.scheduledStart
  });
  
  // Internal pagination handler that preserves constraints
  const handleNextPageInternal = () => {
    console.log("[MODAL PAGINATION] ============================================");
    console.log("[MODAL PAGINATION] Next button clicked!");
    console.log("[MODAL PAGINATION] Current page:", page);
    console.log("[MODAL PAGINATION] MODAL STATE CHECK:");
    console.log("[MODAL PAGINATION]   - activeConstraints:", activeConstraints);
    console.log("[MODAL PAGINATION]   - Locked Date from state:", activeConstraints.lockedDate);
    console.log("[MODAL PAGINATION]   - Strategy from state:", activeConstraints.strategy);
    console.log("[MODAL PAGINATION]   - Duration from state:", activeConstraints.lockedDuration);
    console.log("[MODAL PAGINATION]   - isConflict:", activeConstraints.isConflict);
    
    // CRITICAL: Build preserved constraints object to pass to parent
    // This ensures the modal's state is passed up the component tree
    const preservedConstraints = {
      scheduledStart: activeConstraints.lockedDate || undefined,
      strategy: activeConstraints.strategy || undefined,
      durationMinutes: activeConstraints.lockedDuration || undefined,
    };
    
    console.log("[MODAL PAGINATION] ============================================");
    console.log("[MODAL PAGINATION] PRESERVED CONSTRAINTS TO PASS TO PARENT:");
    console.log("[MODAL PAGINATION]   - scheduledStart:", preservedConstraints.scheduledStart);
    console.log("[MODAL PAGINATION]   - strategy:", preservedConstraints.strategy);
    console.log("[MODAL PAGINATION]   - durationMinutes:", preservedConstraints.durationMinutes);
    
    // CRITICAL: Log what we expect the parent to use
    if (preservedConstraints.scheduledStart) {
      console.log("[MODAL PAGINATION] ✅ Modal passing locked date to parent:", preservedConstraints.scheduledStart);
      console.log("[MODAL PAGINATION] ✅ Parent MUST use this date in pagination request");
    } else {
      console.error("[MODAL PAGINATION] ❌ Modal has NO locked date to pass!");
      console.error("[MODAL PAGINATION] ❌ Pagination will fail!");
    }
    
    console.log("[MODAL PAGINATION] Calling parent's onRefresh with preserved constraints...");
    console.log("[MODAL PAGINATION] ============================================");
    
    // If parent provides onRefresh, use it with preserved constraints
    if (onRefresh) {
      onRefresh(preservedConstraints);
    } else {
      console.warn("[MODAL PAGINATION] No onRefresh callback provided - pagination will not work");
    }
  };
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-base-100 rounded-lg shadow-xl w-full max-w-lg p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold">
            {isConflict ? "Resolve Conflict" : "Choose a Time Slot"} {page > 1 && <span className="text-sm opacity-70">- Page {page}</span>}
          </h3>
          <button
            className="btn btn-ghost btn-sm"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Optional Task Metadata */}
        {metadata && (
          <div className="mb-4 text-sm opacity-80">
            <div>
              <b>Title:</b> {metadata.title}
            </div>
            <div>
              <b>Type:</b> {metadata.task_type}
            </div>
            <div>
              <b>Priority:</b> {metadata.priority}
            </div>
            {metadata.durationMinutes ? (
              <div>
                <b>Duration:</b> {metadata.durationMinutes} minutes
              </div>
            ) : (
              <div>
                <b>Duration:</b> from suggested start/end
              </div>
            )}
          </div>
        )}

        {/* Suggestions List */}
        <div className="space-y-3 min-h-[420px] relative">
          {isLoading && (
            <div className="absolute inset-0 bg-base-100/80 flex items-center justify-center z-10 rounded-lg">
              <div className="flex flex-col items-center gap-2">
                <div className="loading loading-spinner loading-lg"></div>
                <span className="text-sm">Loading suggestions...</span>
              </div>
            </div>
          )}
          
          {suggestions.length === 0 ? (
            <div className="text-center text-base-content/60 py-4">
              No suggestions available
            </div>
          ) : (
            suggestions.map((s, idx) => (
              <div key={`${s.scheduledStart}-${s.scheduledEnd}-page${page}-${idx}`} className="card bg-base-200">
                <div className="card-body flex-row items-center justify-between">
                  <div className="flex flex-col gap-2 flex-1">
                    <DateTimeRangeBadges start={s.scheduledStart} end={s.scheduledEnd} />
                    
                    {/* Workday Warning */}
                    {s.exceedsWorkHours && (
                      <div className="alert alert-warning py-2 px-3 text-sm">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="w-4 h-4"
                        >
                          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                          <line x1="12" y1="9" x2="12" y2="13"></line>
                          <line x1="12" y1="17" x2="12.01" y2="17"></line>
                        </svg>
                        <span className="font-medium">⚠️ Exceeds your defined work hours</span>
                      </div>
                    )}
                    
                    {typeof s.score === "number" && (
                      <span className="text-xs opacity-70">
                        Score: {s.score}
                      </span>
                    )}
                  </div>
                  <button
                    className="btn btn-success btn-sm"
                    onClick={() => {
                      console.log("[MODAL DEBUG] Choose button clicked for suggestion:", s);
                      console.log("[MODAL DEBUG] Calling onSelect with suggestion");
                      onSelect(s);
                    }}
                  >
                    Choose
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Action Buttons */}
        <div className="mt-4 flex gap-2 justify-between items-center">
          {/* Left side: Cancel and Back to Options */}
          <div className="flex gap-2">
            <button className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            
            {/* Only show Change Slots button for conflict resolution flow */}
            {isConflict && onBackToOptions && (
              <button 
                className="btn btn-ghost btn-sm"
                onClick={() => {
                  console.log("[MODAL DEBUG] Back to Options clicked");
                  onBackToOptions();
                }}
                disabled={isLoading}
                title="Return to strategy selection"
              >
                ← Change Slots
              </button>
            )}
          </div>
          
          {/* Right side: Pagination Controls */}
          {(onPrevious || onRefresh) && (
            <div className="flex gap-2">
              {onPrevious && (
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => {
                    console.log("[MODAL DEBUG] Previous button clicked");
                    console.log("[MODAL DEBUG] Current page:", page);
                    console.log("[MODAL DEBUG] Calling onPrevious");
                    onPrevious();
                  }}
                  disabled={page === 1 || isLoading}
                  title="Go to previous page"
                >
                  &lt; Previous
                </button>
              )}
              
              {/* Page Indicator */}
              <span className="flex items-center px-3 text-sm font-medium">
                Page {page}
              </span>
              
              {onRefresh && (
                <button
                  className={`btn btn-primary btn-sm ${isLoading ? "loading" : ""}`}
                  onClick={() => {
                    console.log("[MODAL DEBUG] Next button clicked");
                    console.log("[MODAL DEBUG] Current page:", page);
                    console.log("[MODAL DEBUG] Suggestions count:", suggestions.length);
                    console.log("[MODAL DEBUG] isLoading:", isLoading);
                    console.log("[MODAL DEBUG] hasMorePages:", hasMorePages);
                    console.log("[MODAL DEBUG] Active constraints:", activeConstraints);
                    console.log("[MODAL DEBUG] Calling handleNextPageInternal");
                    handleNextPageInternal();
                  }}
                  disabled={isLoading || !hasMorePages || suggestions.length < 3}
                  title={
                    !hasMorePages || suggestions.length < 3 
                      ? "No more suggestions available" 
                      : "Go to next page"
                  }
                >
                  {isLoading ? "Loading..." : "Next >"}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SuggestionSelectionModal;
