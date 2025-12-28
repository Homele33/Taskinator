import React from "react";
import { formatDate, formatTime, formatDateTime, formatTimeRange } from "@/utils/dateFormat";

/**
 * Calendar SVG Icon
 */
export const CalendarIcon: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
    <line x1="16" y1="2" x2="16" y2="6"></line>
    <line x1="8" y1="2" x2="8" y2="6"></line>
    <line x1="3" y1="10" x2="21" y2="10"></line>
  </svg>
);

/**
 * Clock SVG Icon
 */
export const ClockIcon: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <polyline points="12 6 12 12 16 14"></polyline>
  </svg>
);

/**
 * Date Badge Component - Modern badge with calendar icon
 */
export const DateBadge: React.FC<{ date: Date | string | null | undefined; className?: string }> = ({ date, className = "" }) => {
  if (!date) return null;
  const formatted = formatDate(date);
  if (!formatted) return null;
  
  return (
    <div className={`badge badge-outline gap-1 ${className}`}>
      <CalendarIcon className="w-3 h-3" />
      {formatted}
    </div>
  );
};

/**
 * Time Range Badge Component - Modern badge with clock icon
 */
export const TimeRangeBadge: React.FC<{ start: Date | string | null | undefined; end: Date | string | null | undefined; className?: string }> = ({ start, end, className = "" }) => {
  if (!start) return null;
  const formatted = formatTimeRange(start, end);
  if (!formatted) return null;
  
  return (
    <div className={`badge badge-ghost gap-1 ${className}`}>
      <ClockIcon className="w-3 h-3" />
      {formatted}
    </div>
  );
};

/**
 * DateTime Badge Component - Combined date and time badge
 */
export const DateTimeBadge: React.FC<{ datetime: Date | string | null | undefined; className?: string }> = ({ datetime, className = "" }) => {
  if (!datetime) return null;
  const formatted = formatDateTime(datetime);
  if (!formatted) return null;
  
  return (
    <div className={`badge badge-outline gap-1 ${className}`}>
      <CalendarIcon className="w-3 h-3" />
      {formatted}
    </div>
  );
};

/**
 * Combined Date and Time Badges - Modern two-badge display
 */
export const DateTimeRangeBadges: React.FC<{ start: Date | string | null | undefined; end: Date | string | null | undefined; className?: string }> = ({ start, end, className = "" }) => {
  if (!start) return null;
  
  return (
    <div className={`flex gap-2 items-center ${className}`}>
      <DateBadge date={start} />
      <TimeRangeBadge start={start} end={end} />
    </div>
  );
};
