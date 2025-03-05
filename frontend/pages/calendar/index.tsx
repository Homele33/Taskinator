import React, { useState, useEffect } from "react";
import { Subtask, Task } from "@/components/task";
import { fetchTasks } from "@/utils/taskUtils";

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
    getTasks();
  },[]);

  const getTasks = async () => {
    try{
        const data = await fetchTasks();
        setTasks(data.tasks);
    }
   catch (err) {
    console.error("Error fetching tasks:", err);
   }
  }


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
      calendarDays.forEach((calDay) => {
        const dateString: string = `${calDay.year}-${String(
          calDay.month + 1
        ).padStart(2, "0")}-${String(calDay.day).padStart(2, "0")}`;
        calDay.tasks = tasks.filter((task) => task.dueDate === dateString);
      });

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
  }, [calendar]);

  // Render task details
  const renderTaskDetails = (task: Task) => {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h4 className="text-lg font-semibold">{task.title}</h4>
            <div className="flex gap-2 mt-1">
              <span className={statusClasses[task.status]}>
                {task.status.replace("_", " ")}
              </span>
              <span
                className={`badge ${
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
          </div>
          <button onClick={handleBackToList} className="btn btn-sm btn-ghost">
            Back
          </button>
        </div>

        {task.description && (
          <div className="mt-4">
            <h5 className="text-sm font-medium opacity-70">Description</h5>
            <p className="mt-1">{task.description}</p>
          </div>
        )}

        {task.dueDate && (
          <div className="mt-2">
            <h5 className="text-sm font-medium opacity-70">Due Date</h5>
            <p className="mt-1">
              {new Date(task.dueDate).toLocaleDateString()}
            </p>
          </div>
        )}

        {task.subtasks.length > 0 && (
          <div className="mt-4">
            <h5 className="text-sm font-medium opacity-70">Subtasks</h5>
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
                      <p className="text-xs opacity-70 mt-1">
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

  // Render task list
  const renderTaskList = () => {
    return (
      <>
        <h3 className="card-title">
          {selectedDay
            ? `Tasks for ${monthNames[selectedDay.month]} ${selectedDay.day}, ${
                selectedDay.year
              }`
            : "Select a day to view tasks"}
        </h3>

        {selectedDay &&
          (dayTasks.length > 0 ? (
            <ul className="menu p-0">
              {dayTasks.map((task) => (
                <li key={task.id}>
                  <button
                    onClick={() => handleTaskClick(task)}
                    className="border-b border-base-300 py-2 hover:bg-base-300 w-full text-left"
                  >
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center">
                        <span
                          className={`w-3 h-3 rounded-full mr-2 ${
                            task.priority === "HIGH"
                              ? "bg-error"
                              : task.priority === "MEDIUM"
                              ? "bg-warning"
                              : "bg-success"
                          }`}
                        ></span>
                        <span>{task.title}</span>
                      </div>
                      <span className={`${statusClasses[task.status]} ml-2`}>
                        {}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-base-content opacity-70">
              No tasks scheduled for this day.
            </p>
          ))}

        {!selectedDay && (
          <div className="flex items-center justify-center h-32 opacity-50">
            <p>Click on a date to view tasks</p>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="flex flex-col lg:flex-row gap-4 max-w-6xl mx-auto p-4" data-theme="">
      {/* Calendar Section */}
      <div className="card bg-base-200 shadow-xl lg:w-2/3">
        <div className="card-body p-4">
          <div className="flex items-center justify-between pb-4 border-b border-base-300">
            <div>
              <h2 className="card-title text-xl">
                {monthNames[currentMonth]} {currentYear}
              </h2>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={goToPrevMonth}
                className="btn btn-circle btn-sm btn-ghost"
              >
                &lt;
              </button>
              <button onClick={goToToday} className="btn btn-sm">
                Today
              </button>
              <button
                onClick={goToNextMonth}
                className="btn btn-circle btn-sm btn-ghost"
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
                className="text-center py-2 text-sm font-medium border-b border-base-300"
              >
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {calendar.map((day, index) => (
              <div
                key={index}
                onClick={() => handleDayClick(day)}
                className={`min-h-24 p-1 border border-base-300 ${
                  !day.isCurrentMonth ? "opacity-50" : ""
                } ${
                  selectedDay?.day === day.day &&
                  selectedDay?.month === day.month &&
                  selectedDay?.year === day.year
                    ? "border-primary border-2"
                    : ""
                } hover:bg-base-300 cursor-pointer`}
              >
                <div className="flex justify-between">
                  <span
                    className={`text-sm ${
                      new Date().getDate() === day.day &&
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
                        className={`${
                          priorityClasses[task.priority]
                        } text-xs p-1 mb-1 rounded truncate`}
                      >
                        {task.title}
                      </div>
                    ))}
                  {day.tasks && day.tasks.length > 2 && (
                    <div className="text-xs opacity-70">
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
