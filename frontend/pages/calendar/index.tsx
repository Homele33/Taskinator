import React, { useState, useEffect } from "react";
import { Task } from "@/components/tasksTypes";
import { fetchTasks } from "@/utils/taskUtils";
import { DateTimeRangeBadges, DateTimeBadge, TimeRangeBadge } from "@/components/DateBadges";
import { formatTime } from "@/utils/dateFormat";

interface CalendarDay {
  day: number;
  month: number;
  year: number;
  isCurrentMonth: boolean;
  tasks?: Task[];
}

interface TaskCalendarProps {
  initialTasks?: Task[];
}

const TaskCalendar: React.FC<TaskCalendarProps> = ({ initialTasks = [] }) => {
  // Sample tasks - replace with your actual task data
  const [tasks, setTasks] = useState<Task[]>(
    initialTasks.length > 0 ? initialTasks : []
  );

  useEffect(() => {
    const theme = localStorage.getItem("theme") || "default";
    document.documentElement.setAttribute("data-theme", theme);
    getTasks();
  }, []);

  const getTasks = async () => {
    console.log("[CALENDAR FETCH] ============================================");
    console.log("[CALENDAR FETCH] Fetching tasks for calendar view...");
    try {
      const data = await fetchTasks();
      console.log("[CALENDAR FETCH] Received tasks:", data.tasks?.length || 0);
      console.log("[CALENDAR FETCH] Task IDs:", data.tasks?.map((t: Task) => t.id));
      console.log("[CALENDAR FETCH] Tasks with dates:");
      data.tasks?.forEach((task: Task) => {
        if (task.scheduledStart || task.dueDate) {
          console.log(`[CALENDAR FETCH]   - Task ${task.id}: ${task.title}`);
          console.log(`[CALENDAR FETCH]     Scheduled Start: ${task.scheduledStart}`);
          console.log(`[CALENDAR FETCH]     Due Date: ${task.dueDate}`);
        }
      });
      setTasks(data.tasks);
      console.log("[CALENDAR FETCH] ✅ Calendar tasks state updated");
    } catch (err) {
      console.error("[CALENDAR FETCH] ❌ Error fetching tasks:", err);
    }
    console.log("[CALENDAR FETCH] ============================================");
  };

  // State for current date display
  const [currentMonth, setCurrentMonth] = useState<number>(
    new Date().getMonth()
  );
  const [currentYear, setCurrentYear] = useState<number>(
    new Date().getFullYear()
  );
  const [calendar, setCalendar] = useState<CalendarDay[]>([]);
  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null);
  const [dayTasks, setDayTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  // Month names for display
  const monthNames: string[] = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  // Day names for display
  const dayNames: string[] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // Priority indicators with daisyUI classes
  const priorityClasses: Record<string, string> = {
    HIGH: "border border-error",
    MEDIUM: "border border-warning",
    LOW: "border border-info",
  };

  const statusClasses: Record<string, string> = {
    TODO: "badge badge-ghost",
    IN_PROGRESS: "badge badge-primary",
    COMPLETED: "badge badge-success",
  };

  // Generate calendar data
  useEffect(() => {
    const generateCalendar = (): void => {
      // First day of the month
      const firstDay: Date = new Date(currentYear, currentMonth, 1);
      // Last day of the month
      const lastDay: Date = new Date(currentYear, currentMonth + 1, 0);

      // Calculate days from previous month to fill first week
      const startingDayOfWeek: number = firstDay.getDay();

      // Calculate total days in calendar view (up to 6 weeks)
      const totalDays: number = 42; // 6 weeks

      const calendarDays: CalendarDay[] = [];

      // Previous month days
      const prevMonthLastDay: number = new Date(
        currentYear,
        currentMonth,
        0
      ).getDate();
      for (let i: number = startingDayOfWeek - 1; i >= 0; i--) {
        calendarDays.push({
          day: prevMonthLastDay - i,
          month: currentMonth - 1,
          year: currentYear,
          isCurrentMonth: false,
        });
      }

      // Current month days
      for (let i: number = 1; i <= lastDay.getDate(); i++) {
        calendarDays.push({
          day: i,
          month: currentMonth,
          year: currentYear,
          isCurrentMonth: true,
        });
      }

      // Next month days
      const remainingDays: number = totalDays - calendarDays.length;
      for (let i: number = 1; i <= remainingDays; i++) {
        calendarDays.push({
          day: i,
          month: currentMonth + 1,
          year: currentYear,
          isCurrentMonth: false,
        });
      }

      // Add tasks to calendar days
      console.log("[CALENDAR RENDER] ============================================");
      console.log("[CALENDAR RENDER] Assigning tasks to calendar days");
      console.log("[CALENDAR RENDER] Current month:", monthNames[currentMonth], currentYear);
      console.log("[CALENDAR RENDER] Total tasks to assign:", tasks.length);
      
      calendarDays.forEach((calDay) => {
        const dateString: string = `${calDay.year}-${String(
          calDay.month + 1
        ).padStart(2, "0")}-${String(calDay.day).padStart(2, "0")}`;

        // CRITICAL FIX: Check both dueDate AND scheduledStart for task assignment
        // Rule 4 tasks may have scheduledStart but not dueDate
        calDay.tasks = tasks.filter((task) => {
          const dueDateMatch = task.dueDate?.split("T")[0] === dateString;
          const scheduledStartMatch = task.scheduledStart?.split("T")[0] === dateString;
          
          if (dueDateMatch || scheduledStartMatch) {
            console.log(`[CALENDAR RENDER] ✅ Task ${task.id} assigned to ${dateString}`);
            console.log(`[CALENDAR RENDER]   - Title: ${task.title}`);
            console.log(`[CALENDAR RENDER]   - Due Date: ${task.dueDate}`);
            console.log(`[CALENDAR RENDER]   - Scheduled Start: ${task.scheduledStart}`);
          }
          
          return dueDateMatch || scheduledStartMatch;
        });
      });
      
      console.log("[CALENDAR RENDER] ============================================");

      setCalendar(calendarDays);
    };

    generateCalendar();
  }, [currentMonth, currentYear, tasks]);

  // Handle month navigation
  const goToPrevMonth = (): void => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const goToNextMonth = (): void => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  // Handle day selection
  const handleDayClick = (day: CalendarDay): void => {
    setSelectedDay(day);
    setDayTasks(day.tasks || []);
    setSelectedTask(null); // Clear selected task when changing days
  };

  // Handle task selection
  const handleTaskClick = (task: Task): void => {
    setSelectedTask(task);
  };

  // Go back to task list
  const handleBackToList = (): void => {
    setSelectedTask(null);
  };

  // Today button handler
  const goToToday = (): void => {
    const today: Date = new Date();
    setCurrentMonth(today.getMonth());
    setCurrentYear(today.getFullYear());

    // Find and select today in the calendar
    const todayDate = `${today.getFullYear()}-${String(
      today.getMonth() + 1
    ).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
    const todayTasks = tasks.filter((task) => task.dueDate === todayDate);

    // Create a CalendarDay object for today
    const todayCalendarDay: CalendarDay = {
      day: today.getDate(),
      month: today.getMonth(),
      year: today.getFullYear(),
      isCurrentMonth: true,
      tasks: todayTasks,
    };

    setSelectedDay(todayCalendarDay);
    setDayTasks(todayTasks);
    setSelectedTask(null);
  };

  // Set initial selection to today
  useEffect(() => {
    if (!selectedDay && calendar.length > 0) {
      const today = new Date();
      const todayInCalendar = calendar.find(
        (day) =>
          day.day === today.getDate() &&
          day.month === today.getMonth() &&
          day.year === today.getFullYear()
      );

      if (todayInCalendar) {
        handleDayClick(todayInCalendar);
      } else {
        // If today is not in the current view, select the first day of the current month
        const firstCurrentMonthDay = calendar.find((day) => day.isCurrentMonth);
        if (firstCurrentMonthDay) {
          handleDayClick(firstCurrentMonthDay);
        }
      }
    }
  }, [calendar, selectedDay]);

  // Render task details
  const renderTaskDetails = (task: Task) => {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h4 className="text-lg text-base-content font-semibold">
              {task.title}
            </h4>
            <div className="flex gap-2 mt-1">
              <span className={statusClasses[task.status]}>
                {task.status.replace("_", " ")}
              </span>
              <span
                className={`badge ${task.priority === "HIGH"
                  ? "badge-error"
                  : task.priority === "MEDIUM"
                    ? "badge-warning"
                    : "badge-info"
                  }`}
              >
                {task.priority}
              </span>
            </div>
          </div>
          <button onClick={handleBackToList} className="btn btn-sm btn-ghost">
            Back
          </button>
        </div>

        {task.description && (
          <div className="mt-4">
            <h5 className="text-sm text-base-content font-medium opacity-70">
              Description
            </h5>
            <p className="mt-1">{task.description}</p>
          </div>
        )}

        {/* Show scheduled time if available, otherwise show due date */}
        {(task.scheduledStart || task.scheduledEnd) ? (
          <div className="mt-2">
            <h5 className="text-sm text-base-content font-medium opacity-70 mb-2">
              Scheduled Time
            </h5>
            {task.scheduledStart && task.scheduledEnd ? (
              <DateTimeRangeBadges start={task.scheduledStart} end={task.scheduledEnd} />
            ) : (
              <DateTimeBadge datetime={task.scheduledStart || task.scheduledEnd} />
            )}
          </div>
        ) : task.dueDate ? (
          <div className="mt-2">
            <h5 className="text-sm text-base-content font-medium opacity-70 mb-2">
              Due Date
            </h5>
            <DateTimeBadge datetime={task.dueDate} />
          </div>
        ) : null}

        {task.subtasks.length > 0 && (
          <div className="mt-4">
            <h5 className="text-sm text-base-content font-medium opacity-70">
              Subtasks
            </h5>
            <ul className="mt-2 space-y-2">
              {task.subtasks.map((subtask) => (
                <li key={subtask.id} className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    checked={subtask.isDone}
                    className="checkbox checkbox-sm mt-1"
                    readOnly
                  />
                  <div>
                    <p
                      className={
                        subtask.isDone ? "line-through opacity-60" : ""
                      }
                    >
                      {subtask.title}
                    </p>
                    {subtask.description && (
                      <p className="text-xs text-base-content opacity-70 mt-1">
                        {subtask.description}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  // Get priority color for left border
  const getPriorityBarColor = (priority: string) => {
    switch (priority) {
      case "HIGH":
        return "border-l-error";
      case "MEDIUM":
        return "border-l-warning";
      case "LOW":
        return "border-l-info";
      default:
        return "border-l-base-300";
    }
  };

  // Render task list
  const renderTaskList = () => {
    return (
      <>
        {/* Header */}
        <h3 className="text-xl font-bold text-base-content mb-4">
          {selectedDay
            ? `Tasks for ${monthNames[selectedDay.month]} ${selectedDay.day}, ${selectedDay.year}`
            : "Select a day to view tasks"}
        </h3>

        {/* Task List Container */}
        {selectedDay && (
          <div className="bg-base-200/50 rounded-lg p-4">
            {dayTasks.length > 0 ? (
              <div className="flex flex-col gap-3">
                {dayTasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => handleTaskClick(task)}
                    className={`card bg-base-100 shadow-sm border border-base-300 border-l-4 ${getPriorityBarColor(
                      task.priority
                    )} cursor-pointer hover:shadow-md hover:border-l-8 transition-all duration-200`}
                  >
                    <div className="card-body p-4">
                      {/* Task Title */}
                      <h4 className="font-semibold text-base text-base-content mb-2 truncate">
                        {task.title}
                      </h4>

                      {/* Time Badges */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {task.scheduledStart && task.scheduledEnd ? (
                          <DateTimeRangeBadges
                            start={task.scheduledStart}
                            end={task.scheduledEnd}
                          />
                        ) : task.dueDate ? (
                          <div className="badge badge-outline gap-1 text-xs">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className="w-3 h-3"
                            >
                              <circle cx="12" cy="12" r="10"></circle>
                              <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                            {formatTime(task.dueDate)}
                          </div>
                        ) : null}

                        {/* Priority Badge */}
                        <span
                          className={`badge badge-sm ${
                            task.priority === "HIGH"
                              ? "badge-error"
                              : task.priority === "MEDIUM"
                              ? "badge-warning"
                              : "badge-info"
                          }`}
                        >
                          {task.priority}
                        </span>
                      </div>

                      {/* Status */}
                      <div className="mt-2">
                        <span
                          className={`badge badge-sm ${
                            task.status === "COMPLETED"
                              ? "badge-success"
                              : task.status === "IN_PROGRESS"
                              ? "badge-primary"
                              : "badge-ghost"
                          }`}
                        >
                          {task.status.replace("_", " ")}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              /* Empty State */
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-16 h-16 text-base-content opacity-30 mb-4"
                >
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                  <line x1="8" y1="14" x2="16" y2="14"></line>
                  <line x1="8" y1="18" x2="13" y2="18"></line>
                </svg>
                <p className="text-base-content opacity-70 text-lg font-medium">
                  No tasks scheduled for this day
                </p>
                <p className="text-base-content opacity-50 text-sm mt-2">
                  Your day is free!
                </p>
              </div>
            )}
          </div>
        )}

        {/* No Day Selected State */}
        {!selectedDay && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-20 h-20 text-base-content opacity-20 mb-4"
            >
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            <p className="text-base-content opacity-50 text-base">
              Click on a date to view tasks
            </p>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="flex flex-col lg:flex-row gap-4 max-w-7xl mx-auto p-4">
      {/* Calendar Section */}
      <div className="card bg-base-200 shadow-xl lg:w-2/3">
        <div className="card-body p-4">
          <div className="flex items-center justify-between pb-4 border-b border-base-300">
            <div>
              <h2 className="card-title text-xl text-base-content font-semibold">
                {monthNames[currentMonth]} {currentYear}
              </h2>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={goToPrevMonth}
                className="btn btn-circle btn-sm btn-ghost text-base-content"
              >
                &lt;
              </button>
              <button onClick={goToToday} className="btn btn-sm">
                Today
              </button>
              <button
                onClick={goToNextMonth}
                className="btn btn-circle btn-sm btn-ghost text-base-content"
              >
                &gt;
              </button>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-px mt-4">
            {/* Day headers */}
            {dayNames.map((day, index) => (
              <div
                key={index}
                className="text-center py-2 text-sm font-medium border-b border-base-300 text-base-content"
              >
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {calendar.map((day, index) => (
              <div
                key={index}
                onClick={() => handleDayClick(day)}
                className={`min-h-24 p-1 border border-base-300 ${!day.isCurrentMonth ? "opacity-50" : ""
                  } ${selectedDay?.day === day.day &&
                    selectedDay?.month === day.month &&
                    selectedDay?.year === day.year
                    ? "border-primary border-2"
                    : ""
                  } hover:bg-base-300 cursor-pointer`}
              >
                <div className="flex justify-between">
                  <span
                    className={`text-sm text-base-content ${new Date().getDate() === day.day &&
                      new Date().getMonth() === day.month &&
                      new Date().getFullYear() === day.year
                      ? "badge badge-primary rounded-full flex items-center justify-center"
                      : ""
                      }`}
                  >
                    {day.day}
                  </span>
                </div>

                {/* Task indicators */}
                <div className="mt-1 overflow-y-auto max-h-16">
                  {day.tasks &&
                    day.tasks.slice(0, 2).map((task) => (
                      <div
                        key={task.id}
                        className={`${priorityClasses[task.priority]
                          } text-xs p-1 mb-1 rounded truncate text-base-content`}
                      >
                        {task.title}
                      </div>
                    ))}
                  {day.tasks && day.tasks.length > 2 && (
                    <div className="text-xs opacity-70 text-base-content">
                      +{day.tasks.length - 2} more
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Task Details Section */}
      <div className="card bg-base-200 shadow-xl lg:w-1/3">
        <div className="card-body">
          {selectedTask ? renderTaskDetails(selectedTask) : renderTaskList()}
        </div>
      </div>
    </div>
  );
};

export default TaskCalendar;
