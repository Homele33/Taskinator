This is a student project for the final year By Eden Cohen and Dor Biton

# Schedule Organizer

A desktop application for managing tasks, schedules, and reminders built with Python and Tkinter.

## Features

- **Task Management**
  - Create and manage tasks with titles, descriptions, and due dates
  - Set task priorities (High, Medium, Low)
  - Categorize tasks (Work, Personal, Study, Health, Other)
  - Add subtasks to break down complex tasks
  - Track task completion status and progress

- **Calendar View**
  - Visual calendar interface for task management
  - Date-based task filtering
  - Easy task browsing by date

- **User Interface**
  - Modern and clean interface
  - Easy-to-use task creation window
  - Task filtering by category
  - Progress tracking for tasks with subtasks
  - Hierarchical view of tasks and subtasks

- **Reminders**
  - Automatic task reminders
  - Customizable reminder times
  - Desktop notifications for upcoming tasks

## Requirements

- Python 3.8 or higher
- Required Python packages:
  ```
  tkinter (usually comes with Python)
  tkcalendar
  plyer
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd schedule-organizer
   ```

2. Install required packages:
   ```bash
   pip install tkcalendar plyer
   ```

3. Run the application:
   ```bash
   python TaskManager.py
   ```

## Usage

### Creating a New Task

1. Click the "New Task" button in the top right corner
2. Fill in the task details:
   - Task name (required)
   - Description (optional)
   - Due date and time
   - Category
   - Priority
3. Add subtasks if needed
4. Click "Add Task" to save

### Managing Tasks

- **View Tasks**: All tasks are displayed in the main window
- **Filter Tasks**: Use the category dropdown to filter tasks
- **Complete Tasks**: Double-click a task to mark it as complete
- **Delete Tasks**: Select a task and click "Delete Selected"
- **Clear Completed**: Remove all completed tasks with one click

### Calendar View

1. Switch to the Calendar tab
2. Select any date to view tasks due on that day
3. Tasks are displayed with their times and details below the calendar

### Task Details

- **Main Task**
  - Name
  - Description
  - Due Date and Time
  - Category
  - Priority
  - Completion Status
  - Progress (for tasks with subtasks)

- **Subtasks**
  - Name
  - Status
  - Parent Task Association

## Data Storage

- Tasks are automatically saved to `tasks.json`
- Data persists between application sessions
- Automatic backup before modifications (coming soon)
