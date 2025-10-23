import React, { useState } from "react";
import apiClient from "@/api/axiosClient";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSaved?: () => void;
  hideCancel?: boolean;
};

// One-time onboarding form for user preferences
const OnboardingModal: React.FC<Props> = ({ isOpen, onClose, onSaved, hideCancel }) => {
  const [daysOff, setDaysOff] = useState<number[]>([]);
  const [workdayStart, setWorkdayStart] = useState("09:00");
  const [workdayEnd, setWorkdayEnd] = useState("17:00");
  const [focusStart, setFocusStart] = useState<string>(""); 
  const [focusEnd, setFocusEnd] = useState<string>("");     
  const [deadlineBehavior, setDeadlineBehavior] = useState<
    "" | "EARLY" | "ON_TIME" | "LAST_MINUTE"
  >("");
  const [flexibility, setFlexibility] = useState<"" | "LOW" | "MEDIUM" | "HIGH">("");
  const [defaultDuration, setDefaultDuration] = useState(60);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const toggleDay = (d: number) => {
    setDaysOff((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
    );
  };

  // Simple time comparison "HH:MM" → minutes
  const toMinutes = (t: string) => {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + (m || 0);
  };

  const validate = (): string | null => {
    if (!workdayStart || !workdayEnd) return "Workday start/end are required.";
    if (toMinutes(workdayEnd) <= toMinutes(workdayStart))
      return "Workday end must be after start.";
    if (defaultDuration <= 0) return "Default duration must be a positive number.";

    // focus window is optional, but if both provided, check order
    if (focusStart && focusEnd) {
      if (toMinutes(focusEnd) <= toMinutes(focusStart))
        return "Focus end must be after focus start.";
    }
    return null;
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const msg = validate();
    if (msg) {
      setSaving(false);
      setError(msg);
      return;
    }

    try {
      const payload = {
        daysOff,
        workdayPrefStart: workdayStart,
        workdayPrefEnd: workdayEnd,
        focusPeakStart: focusStart || null, // optional
        focusPeakEnd: focusEnd || null,     // optional
        defaultDurationMinutes: defaultDuration,
        deadlineBehavior: (deadlineBehavior || null) as
          | null
          | "EARLY"
          | "ON_TIME"
          | "LAST_MINUTE",
        flexibility: (flexibility || null) as null | "LOW" | "MEDIUM" | "HIGH",
      };

      await apiClient.put("/preferences", payload); // backend enforces one-time (409 on second try)
      onSaved?.();
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.message || "Failed to save preferences.");
    } finally {
      setSaving(false);
    }
  };

  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-base-100 rounded-xl shadow-xl w-full max-w-2xl">
        <form onSubmit={handleSave} className="p-6 space-y-5">
          <h2 className="text-xl font-bold">Welcome! Let’s set your preferences</h2>

          {error && <div className="alert alert-error">{error}</div>}

          {/* Days off */}
          <div className="space-y-2">
            <div className="font-medium">Days off</div>
            <div className="flex flex-wrap gap-2">
              {dayNames.map((label, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => toggleDay(idx)}
                  className={`btn btn-sm ${daysOff.includes(idx) ? "btn-primary" : "btn-outline"}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Workday window */}
          <div className="grid grid-cols-2 gap-4">
            <div className="form-control">
              <label className="label"><span className="label-text">Workday start</span></label>
              <input
                type="time"
                className="input input-bordered w-full"
                value={workdayStart}
                onChange={(e) => setWorkdayStart(e.target.value)}
                required
              />
            </div>
            <div className="form-control">
              <label className="label"><span className="label-text">Workday end</span></label>
              <input
                type="time"
                className="input input-bordered w-full"
                value={workdayEnd}
                onChange={(e) => setWorkdayEnd(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Focus peak (optional) */}
          <div className="space-y-2">
            <div className="font-medium">Peak focus window (optional)</div>
            <div className="grid grid-cols-2 gap-4">
              <div className="form-control">
                <label className="label"><span className="label-text">Focus start</span></label>
                <input
                  type="time"
                  className="input input-bordered w-full"
                  value={focusStart}
                  onChange={(e) => setFocusStart(e.target.value)}
                />
              </div>
              <div className="form-control">
                <label className="label"><span className="label-text">Focus end</span></label>
                <input
                  type="time"
                  className="input input-bordered w-full"
                  value={focusEnd}
                  onChange={(e) => setFocusEnd(e.target.value)}
                />
              </div>
            </div>
            <div className="text-xs opacity-70">
              Leave empty if you don’t have a specific high-focus window.
            </div>
          </div>

          {/* Deadline behavior */}
          <div className="form-control">
            <label className="label"><span className="label-text">How do you usually handle deadlines?</span></label>
            <select
              className="select select-bordered w-full"
              value={deadlineBehavior}
              onChange={(e) =>
                setDeadlineBehavior(e.target.value as "EARLY" | "ON_TIME" | "LAST_MINUTE" | "")
              }
            >
              <option value="">Choose…</option>
              <option value="EARLY">Prefer finishing early</option>
              <option value="ON_TIME">On time is fine</option>
              <option value="LAST_MINUTE">Often last minute</option>
            </select>
          </div>

          {/* Flexibility */}
          <div className="form-control">
            <label className="label"><span className="label-text">Scheduling flexibility</span></label>
            <select
              className="select select-bordered w-full"
              value={flexibility}
              onChange={(e) =>
                setFlexibility(e.target.value as "LOW" | "MEDIUM" | "HIGH" | "")
              }
            >
              <option value="">Choose…</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
          </div>

          {/* Default duration */}
          <div className="form-control">
            <label className="label"><span className="label-text">Default task duration (minutes)</span></label>
            <input
              type="number"
              min={1}
              className="input input-bordered w-full"
              value={defaultDuration}
              onChange={(e) => setDefaultDuration(Number(e.target.value))}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            {!hideCancel ? (
              <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
                Cancel
              </button>
            ) : null}
            <button type="submit" className={`btn btn-primary ${saving ? "loading" : ""}`} disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default OnboardingModal;
