import React, { useMemo, useReducer, useCallback, useEffect } from "react";
import { useRouter } from "next/router";
import { submitPreferences } from "@/utils/taskUtils";

// Constants outside component to avoid recomputation
const TIME_OPTIONS = Array.from({ length: 48 }, (_, i) => {
  const hour = Math.floor(i / 2);
  const min = (i % 2) * 30;
  return `${hour.toString().padStart(2, "0")}:${min
    .toString()
    .padStart(2, "0")}`;
});
const TASK_TYPES = ["Meeting", "Training", "Studies"] as const;
const PRIORITIES = ["Low", "Medium", "High"] as const;
const DAYS_OF_WEEK = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
] as const;

// Discriminated unions for question types
type TaskQuestion = {
  type: "task";
  task: (typeof TASK_TYPES)[number];
  priority: (typeof PRIORITIES)[number];
};
type PreferenceTimeQuestion = { type: "preferenceTime" };
type PreferredDaysQuestion = { type: "preferredDays" };
type FocusHoursQuestion = { type: "focusHours" };
type AvoidTimesQuestion = { type: "avoidTimes" };
type TaskDaysQuestion = { type: "taskDays"; task: (typeof TASK_TYPES)[number] };

type Question =
  | TaskQuestion
  | PreferenceTimeQuestion
  | PreferredDaysQuestion
  | FocusHoursQuestion
  | AvoidTimesQuestion
  | TaskDaysQuestion;

// Build combination list once
const COMBINATIONS: Question[] = [
  ...TASK_TYPES.flatMap((task) =>
    PRIORITIES.map(
      (priority) => ({ type: "task", task, priority } as TaskQuestion)
    )
  ),
  { type: "preferenceTime" },
  { type: "preferredDays" },
  { type: "focusHours" },
  { type: "avoidTimes" },
  ...TASK_TYPES.map((task) => ({ type: "taskDays", task } as TaskDaysQuestion)),
];

interface State {
  currentIndex: number;
  answers: Record<string, { start: string; end: string }>;
  preferenceTime: string;
  preferredDays: string[];
  preferredDaysByTask: Record<string, string[]>;
  startTime: string;
  endTime: string;
  error: string;
  submitted: boolean;
}

type Action =
  | { type: "SET_RANGE"; key: string; start: string; end: string }
  | { type: "SET_PREFERENCE_TIME"; value: string }
  | { type: "TOGGLE_DAY"; day: string }
  | { type: "TOGGLE_TASK_DAY"; task: string; day: string }
  | { type: "SET_INDEX"; index: number }
  | { type: "SET_START_END"; start: string; end: string }
  | { type: "SET_ERROR"; error: string }
  | { type: "SUBMIT" };

const initialState: State = {
  currentIndex: 0,
  answers: {},
  preferenceTime: "",
  preferredDays: [],
  preferredDaysByTask: {},
  startTime: "",
  endTime: "",
  error: "",
  submitted: false,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_RANGE":
      return {
        ...state,
        answers: {
          ...state.answers,
          [action.key]: { start: action.start, end: action.end },
        },
        error: "",
      };
    case "SET_PREFERENCE_TIME":
      return { ...state, preferenceTime: action.value };
    case "TOGGLE_DAY":
      return {
        ...state,
        preferredDays: state.preferredDays.includes(action.day)
          ? state.preferredDays.filter((d) => d !== action.day)
          : [...state.preferredDays, action.day],
      };
    case "TOGGLE_TASK_DAY":
      const currentDays = state.preferredDaysByTask[action.task] || [];
      return {
        ...state,
        preferredDaysByTask: {
          ...state.preferredDaysByTask,
          [action.task]: currentDays.includes(action.day)
            ? currentDays.filter((d) => d !== action.day)
            : [...currentDays, action.day],
        },
      };
    case "SET_INDEX":
      return { ...state, currentIndex: action.index, error: "" };
    case "SET_START_END":
      return { ...state, startTime: action.start, endTime: action.end };
    case "SET_ERROR":
      return { ...state, error: action.error };
    case "SUBMIT":
      return { ...state, submitted: true };
    default:
      return state;
  }
}

const TimeRangeQuestion: React.FC<{
  label: string;
  start: string;
  end: string;
  onStart: (value: string) => void;
  onEnd: (value: string) => void;
}> = ({ label, start, end, onStart, onEnd }) => (
  <div className="space-y-2">
    <p className="text-base">{label}</p>
    <div className="flex gap-4">
      <select
        aria-label="Start Time"
        className="select select-bordered flex-1"
        value={start}
        onChange={(e) => onStart(e.target.value)}
      >
        <option value="">Select start</option>
        {TIME_OPTIONS.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
      <select
        aria-label="End Time"
        className="select select-bordered flex-1"
        value={end}
        onChange={(e) => onEnd(e.target.value)}
      >
        <option value="">Select end</option>
        {TIME_OPTIONS.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    </div>
  </div>
);

const CheckboxGroup: React.FC<{
  label: string;
  options: readonly string[];
  selected: string[];
  onToggle: (option: string) => void;
}> = ({ label, options, selected, onToggle }) => (
  <div className="space-y-2">
    <p className="text-base">{label}</p>
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <label key={o} className="flex items-center space-x-1 cursor-pointer">
          <input
            type="checkbox"
            aria-label={o}
            checked={selected.includes(o)}
            onChange={() => onToggle(o)}
            className="checkbox checkbox-sm"
          />
          <span>{o}</span>
        </label>
      ))}
    </div>
  </div>
);

const SmartSetupPage: React.FC = () => {
  const router = useRouter();
  const [state, dispatch] = useReducer(reducer, initialState);
  const {
    currentIndex,
    startTime,
    endTime,
    answers,
    preferenceTime,
    preferredDays,
    preferredDaysByTask,
    error,
    submitted,
  } = state;

  useEffect(() => {
    if (submitted) {
      const payload = {
        answers,
        preferenceTime,
        preferredDays,
        preferredDaysByTask,
      };

      submitPreferences(payload)
        .then(() => {
          console.log("Preferences saved successfully");
          dispatch({ type: "SET_ERROR", error: "" }); // Clear any existing errors
          // Wait a short moment to show the success message before redirecting
          setTimeout(() => {
            router.push("/");
          }, 1500);
        })
        .catch((err) => {
          console.error("Error saving preferences:", err);
          dispatch({
            type: "SET_ERROR",
            error: err.message || "Failed to save preferences",
          });
        });
    }
  }, [
    submitted,
    answers,
    preferenceTime,
    preferredDays,
    preferredDaysByTask,
    router,
  ]);

  const current = useMemo(() => COMBINATIONS[currentIndex], [currentIndex]);
  const key = useMemo(() => {
    switch (current.type) {
      case "task":
        return `${current.task}_${current.priority}`;
      case "taskDays":
        return `PreferredDays_${current.task}`;
      default:
        return current.type;
    }
  }, [current]);

  useEffect(() => {
    const existing = answers[key];
    dispatch({
      type: "SET_START_END",
      start: existing?.start || "",
      end: existing?.end || "",
    });
  }, [key]);

  const handleNext = useCallback(() => {
    if (
      current.type === "task" ||
      current.type === "focusHours" ||
      current.type === "avoidTimes"
    ) {
      if (!startTime || !endTime) {
        dispatch({
          type: "SET_ERROR",
          error: "Please select both start and end times.",
        });
        return;
      }
      if (startTime >= endTime) {
        dispatch({
          type: "SET_ERROR",
          error: "End time must be later than start time.",
        });
        return;
      }
      dispatch({ type: "SET_RANGE", key, start: startTime, end: endTime });
    }
    if (currentIndex + 1 < COMBINATIONS.length) {
      dispatch({ type: "SET_INDEX", index: currentIndex + 1 });
    } else {
      dispatch({ type: "SUBMIT" });
    }
  }, [current, key, startTime, endTime, currentIndex]);

  const handleBack = useCallback(() => {
    if (currentIndex > 0)
      dispatch({ type: "SET_INDEX", index: currentIndex - 1 });
  }, [currentIndex]);

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Smart Setup</h1>
      {!submitted ? (
        <>
          {(current.type === "task" ||
            current.type === "focusHours" ||
            current.type === "avoidTimes") && (
            <TimeRangeQuestion
              label={
                current.type === "task"
                  ? `Question ${
                      currentIndex + 1
                    }: When do you usually perform a ${
                      current.task
                    } task with ${current.priority} priority?`
                  : current.type === "focusHours"
                  ? `Question ${
                      currentIndex + 1
                    }: During which hours do you feel most focused?`
                  : `Question ${
                      currentIndex + 1
                    }: Are there any times you'd like to avoid for tasks?`
              }
              start={startTime}
              end={endTime}
              onStart={(val) =>
                dispatch({ type: "SET_START_END", start: val, end: endTime })
              }
              onEnd={(val) =>
                dispatch({ type: "SET_START_END", start: startTime, end: val })
              }
            />
          )}
          {current.type === "preferenceTime" && (
            <div className="form-control">
              <label className="label">
                Question {currentIndex + 1}: What time of day do you prefer for
                tasks?
              </label>
              <select
                aria-label="Preference Time"
                className="select select-bordered"
                value={preferenceTime}
                onChange={(e) =>
                  dispatch({
                    type: "SET_PREFERENCE_TIME",
                    value: e.target.value,
                  })
                }
              >
                <option value="">Select preference</option>
                {["Morning", "Afternoon", "Evening", "No preference"].map(
                  (opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  )
                )}
              </select>
            </div>
          )}
          {current.type === "preferredDays" && (
            <CheckboxGroup
              label={`Question ${
                currentIndex + 1
              }: Which days are preferred for scheduling tasks?`}
              options={DAYS_OF_WEEK}
              selected={preferredDays}
              onToggle={(day) => dispatch({ type: "TOGGLE_DAY", day })}
            />
          )}
          {current.type === "taskDays" && (
            <CheckboxGroup
              label={`Question ${
                currentIndex + 1
              }: Which days are preferred for ${current.task} tasks?`}
              options={DAYS_OF_WEEK}
              selected={preferredDaysByTask[current.task] || []}
              onToggle={(day) =>
                dispatch({ type: "TOGGLE_TASK_DAY", task: current.task, day })
              }
            />
          )}
          {error && <p className="text-red-500 font-medium">{error}</p>}
          <div className="flex justify-between mt-4">
            {currentIndex > 0 && (
              <button onClick={handleBack} className="btn btn-outline btn-info">
                Back
              </button>
            )}
            <button onClick={handleNext} className="btn btn-primary">
              {currentIndex + 1 < COMBINATIONS.length ? "Next" : "Finish"}
            </button>
          </div>
        </>
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-green-600">
            All answers have been submitted!
          </h2>
          <p className="text-gray-600">Redirecting to home page...</p>
        </div>
      )}
    </div>
  );
};

export default SmartSetupPage;
