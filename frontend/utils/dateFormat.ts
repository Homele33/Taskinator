/**
 * Date formatting utilities for DD/MM/YYYY format
 * These functions ensure consistent date display across the application
 * while keeping API communication in ISO format (YYYY-MM-DD)
 */

/**
 * Format date as DD/MM/YYYY
 * @param date - Date object or ISO string
 * @returns Formatted date string (DD/MM/YYYY)
 */
export function formatDate(date: Date | string | null | undefined): string {
  if (!date) return "";
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  
  return `${day}/${month}/${year}`;
}

/**
 * Format time as hh:mm AM/PM (12-hour format)
 * @param date - Date object or ISO string
 * @returns Formatted time string (hh:mm AM/PM)
 */
export function formatTime(date: Date | string | null | undefined): string {
  if (!date) return "";
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  let hours = d.getHours();
  const minutes = String(d.getMinutes()).padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";
  
  // Convert to 12-hour format
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 should be 12
  const hoursStr = String(hours).padStart(2, "0");
  
  return `${hoursStr}:${minutes} ${ampm}`;
}

/**
 * Format date and time as DD/MM/YYYY hh:mm AM/PM
 * @param date - Date object or ISO string
 * @returns Formatted datetime string (DD/MM/YYYY hh:mm AM/PM)
 */
export function formatDateTime(date: Date | string | null | undefined): string {
  if (!date) return "";
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  
  return `${formatDate(d)} ${formatTime(d)}`;
}

/**
 * Format time range showing start and end times
 * @param start - Start date/time
 * @param end - End date/time
 * @returns Formatted time range string (hh:mm AM/PM - hh:mm AM/PM)
 */
export function formatTimeRange(
  start: Date | string | null | undefined,
  end: Date | string | null | undefined
): string {
  if (!start) return "";
  
  const startTime = formatTime(start);
  
  if (!end) return startTime;
  
  const endTime = formatTime(end);
  return `${startTime} - ${endTime}`;
}

/**
 * Format full date and time range
 * @param start - Start date/time
 * @param end - End date/time
 * @returns Formatted datetime range (DD/MM/YYYY HH:MM - HH:MM)
 */
export function formatDateTimeRange(
  start: Date | string | null | undefined,
  end: Date | string | null | undefined
): string {
  if (!start) return "";
  
  const startDate = formatDate(start);
  const startTime = formatTime(start);
  
  if (!end) return `${startDate} ${startTime}`;
  
  const endTime = formatTime(end);
  return `${startDate} ${startTime} - ${endTime}`;
}
