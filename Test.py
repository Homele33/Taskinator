import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta
import os
from tkcalendar import DateEntry, Calendar
import threading
import time
from plyer import notification


class TimeEntry(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Hour selection
        self.hour_var = tk.StringVar()
        self.hour_spinbox = ttk.Spinbox(
            self, from_=0, to=23, width=3,
            format="%02.0f",
            textvariable=self.hour_var
        )
        self.hour_spinbox.set("09")
        self.hour_spinbox.pack(side=tk.LEFT)

        ttk.Label(self, text=":").pack(side=tk.LEFT)

        # Minute selection
        self.minute_var = tk.StringVar()
        self.minute_spinbox = ttk.Spinbox(
            self, from_=0, to=59, width=3,
            format="%02.0f",
            textvariable=self.minute_var
        )
        self.minute_spinbox.set("00")
        self.minute_spinbox.pack(side=tk.LEFT)

    def get_time(self):
        return f"{self.hour_var.get()}:{self.minute_var.get()}"


class NewTaskWindow(tk.Toplevel):
    def __init__(self, parent, categories, callback):
        super().__init__(parent)
        self.callback = callback

        self.title("New Task")
        self.geometry("500x600")

        # Make window modal
        self.transient(parent)
        self.grab_set()

        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Task name
        ttk.Label(main_frame, text="Task Name:").pack(fill=tk.X, pady=(0, 5))
        self.task_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.task_var, width=40).pack(fill=tk.X, pady=(0, 15))

        # Date and time frame
        datetime_frame = ttk.LabelFrame(main_frame, text="Due Date and Time", padding="10")
        datetime_frame.pack(fill=tk.X, pady=(0, 15))

        # Date picker
        ttk.Label(datetime_frame, text="Date:").pack(pady=(0, 5))
        self.date_picker = DateEntry(datetime_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2)
        self.date_picker.pack(pady=(0, 10))

        # Time picker
        ttk.Label(datetime_frame, text="Time:").pack(pady=(0, 5))
        self.time_picker = TimeEntry(datetime_frame)
        self.time_picker.pack(pady=(0, 5))

        # Category and Priority frame
        details_frame = ttk.LabelFrame(main_frame, text="Task Details", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 15))

        # Category
        ttk.Label(details_frame, text="Category:").pack(pady=(0, 5))
        self.category_var = tk.StringVar()
        ttk.Combobox(details_frame, textvariable=self.category_var,
                     values=categories, width=15).pack(pady=(0, 10))
        self.category_var.set("Other")

        # Priority
        ttk.Label(details_frame, text="Priority:").pack(pady=(0, 5))
        self.priority_var = tk.StringVar()
        ttk.Combobox(details_frame, textvariable=self.priority_var,
                     values=["High", "Medium", "Low"], width=15).pack(pady=(0, 10))
        self.priority_var.set("Medium")

        # Reminder frame
        reminder_frame = ttk.LabelFrame(main_frame, text="Reminder", padding="10")
        reminder_frame.pack(fill=tk.X, pady=(0, 15))

        reminder_inner = ttk.Frame(reminder_frame)
        reminder_inner.pack(fill=tk.X)

        self.reminder_var = tk.StringVar()
        ttk.Combobox(reminder_inner, textvariable=self.reminder_var,
                     values=["5", "15", "30", "60", "120"], width=10).pack(side=tk.LEFT, padx=5)
        self.reminder_var.set("30")
        ttk.Label(reminder_inner, text="minutes before").pack(side=tk.LEFT)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Add Task", command=self.submit).pack(side=tk.RIGHT, padx=5)

        # Center the window
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def submit(self):
        task = self.task_var.get().strip()
        date = self.date_picker.get_date().strftime("%Y-%m-%d")
        time = self.time_picker.get_time()

        if not task:
            messagebox.showerror("Error", "Please enter a task name", parent=self)
            return

        task_data = {
            "task": task,
            "due_date": f"{date} {time}",
            "category": self.category_var.get(),
            "priority": self.priority_var.get(),
            "status": "Pending",
            "reminder": self.reminder_var.get()
        }

        self.callback(task_data)
        self.destroy()

class ScheduleOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Schedule Organizer")
        self.root.geometry("1200x800")

        # Define a new style
        style = ttk.Style()
        style.theme_use("clam")  # Use a clean modern theme
        style.configure(
            "TFrame",
            background="#f2f2f2"  # Light gray background
        )
        style.configure(
            "TLabel",
            background="#f2f2f2",
            foreground="#333333",  # Dark text
            font=("Arial", 10)
        )
        style.configure(
            "Header.TLabel",
            font=("Arial", 14, "bold"),
            foreground="#444444"
        )
        style.configure(
            "TButton",
            background="#4caf50",  # Green buttons
            foreground="white",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="raised"
        )
        style.map(
            "TButton",
            background=[("active", "#45a049")],  # Darker green on hover
            relief=[("pressed", "sunken")]
        )
        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            rowheight=25,
            fieldbackground="white"
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold"),
            background="#4caf50",
            foreground="white"
        )

        # Data storage
        self.tasks = []
        self.categories = ["Work", "Personal", "Study", "Health", "Other"]
        self.load_tasks()

        # Create main UI
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self.create_header()
        self.create_tabs()
        self.start_reminder_thread()

    def create_header(self):
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Schedule Organizer", style="Header.TLabel").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        new_task_btn = ttk.Button(btn_frame, text="New Task", command=self.show_new_task_window)
        new_task_btn.pack(side=tk.RIGHT, padx=5)

    def show_new_task_window(self):
        NewTaskWindow(self.root, self.categories, self.add_task)

    def create_frames(self):
        # Input frame
        self.input_frame = ttk.LabelFrame(self.tasks_tab, text="New Task", padding="10")
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)

        # List frame
        self.list_frame = ttk.Frame(self.tasks_tab, padding="10")
        self.list_frame.pack(fill=tk.BOTH, expand=True)

    def create_task_input(self):
        # Task name input
        task_frame = ttk.Frame(self.input_frame)
        task_frame.pack(fill=tk.X, pady=5)

        ttk.Label(task_frame, text="Task:").pack(side=tk.LEFT, padx=5)
        self.task_var = tk.StringVar()
        self.task_entry = ttk.Entry(task_frame, textvariable=self.task_var, width=40)
        self.task_entry.pack(side=tk.LEFT, padx=5)

        # Date and time selection
        datetime_frame = ttk.Frame(self.input_frame)
        datetime_frame.pack(fill=tk.X, pady=5)

        ttk.Label(datetime_frame, text="Due Date:").pack(side=tk.LEFT, padx=5)
        self.date_picker = DateEntry(datetime_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2)
        self.date_picker.pack(side=tk.LEFT, padx=5)

        ttk.Label(datetime_frame, text="Time:").pack(side=tk.LEFT, padx=5)
        self.time_picker = TimeEntry(datetime_frame)
        self.time_picker.pack(side=tk.LEFT, padx=5)

        # Category and priority frame
        cat_pri_frame = ttk.Frame(self.input_frame)
        cat_pri_frame.pack(fill=tk.X, pady=5)

        # Category selection
        ttk.Label(cat_pri_frame, text="Category:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(cat_pri_frame, textvariable=self.category_var,
                                      values=self.categories, width=10)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.set("Other")

        # Priority selection
        ttk.Label(cat_pri_frame, text="Priority:").pack(side=tk.LEFT, padx=5)
        self.priority_var = tk.StringVar()
        priority_combo = ttk.Combobox(cat_pri_frame, textvariable=self.priority_var,
                                      values=["High", "Medium", "Low"], width=10)
        priority_combo.pack(side=tk.LEFT, padx=5)
        priority_combo.set("Medium")

        # Reminder frame
        reminder_frame = ttk.Frame(self.input_frame)
        reminder_frame.pack(fill=tk.X, pady=5)

        ttk.Label(reminder_frame, text="Reminder:").pack(side=tk.LEFT, padx=5)
        self.reminder_var = tk.StringVar()
        reminder_combo = ttk.Combobox(reminder_frame, textvariable=self.reminder_var,
                                      values=["5", "15", "30", "60", "120"], width=10)
        reminder_combo.pack(side=tk.LEFT, padx=5)
        reminder_combo.set("30")
        ttk.Label(reminder_frame, text="minutes before").pack(side=tk.LEFT, padx=5)

        # Add button
        ttk.Button(reminder_frame, text="Add Task", command=self.add_task).pack(side=tk.LEFT, padx=20)

    def create_task_list(self):
        # List container
        list_container = ttk.Frame(self.tasks_tab, padding="10")
        list_container.pack(fill=tk.BOTH, expand=True)

        controls_frame = ttk.Frame(list_container)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.filter_var, values=["All"] + self.categories,
                                    width=15)
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.set("All")
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_task_list())

        ttk.Button(controls_frame, text="Delete Selected", command=self.delete_task).pack(side=tk.RIGHT, padx=5)
        ttk.Button(controls_frame, text="Clear Completed", command=self.clear_completed).pack(side=tk.RIGHT, padx=5)

        # Treeview
        columns = ("Task", "Due Date", "Category", "Priority", "Status")
        self.tree = ttk.Treeview(list_container, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)
    def create_calendar_view(self):
        # Create calendar widget
        self.cal = Calendar(self.calendar_tab, selectmode='day',
                            date_pattern='y-mm-dd')
        self.cal.pack(pady=20, expand=True)

        # Create frame for task list
        self.cal_tasks_frame = ttk.Frame(self.calendar_tab)
        self.cal_tasks_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create task list for selected date
        columns = ("Time", "Task", "Category", "Priority")
        self.cal_tree = ttk.Treeview(self.cal_tasks_frame, columns=columns, show="headings")

        for col in columns:
            self.cal_tree.heading(col, text=col)
            self.cal_tree.column(col, width=150)

        self.cal_tree.pack(fill=tk.BOTH, expand=True)

        # Bind date selection
        self.cal.bind("<<CalendarSelected>>", self.update_calendar_tasks)

    def update_calendar_tasks(self, event=None):
        # Clear current tasks
        for item in self.cal_tree.get_children():
            self.cal_tree.delete(item)

        selected_date = self.cal.get_date()

        # Filter tasks for selected date
        day_tasks = [task for task in self.tasks
                     if task["due_date"].startswith(selected_date)]

        # Sort by time
        day_tasks.sort(key=lambda x: x["due_date"])

        # Add tasks to tree
        for task in day_tasks:
            time = task["due_date"].split()[1] if len(task["due_date"].split()) > 1 else ""
            self.cal_tree.insert("", tk.END, values=(
                time,
                task["task"],
                task["category"],
                task["priority"]
            ))

    def add_task(self, task_data):
        try:
            datetime.strptime(task_data["due_date"], "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid date or time")
            return

        self.tasks.append(task_data)
        self.save_tasks()
        self.refresh_task_list()
        self.update_calendar_tasks()

    def start_reminder_thread(self):
        # Reminder thread logic
        pass

    def check_reminders(self):
        while True:
            current_time = datetime.now()
            for task in self.tasks:
                if task["status"] == "Pending" and task["due_date"]:
                    try:
                        due_time = datetime.strptime(task["due_date"], "%Y-%m-%d %H:%M")
                        reminder_minutes = int(task["reminder"])
                        reminder_time = due_time - timedelta(minutes=reminder_minutes)

                        if current_time >= reminder_time and current_time < reminder_time + timedelta(minutes=1):
                            notification.notify(
                                title="Task Reminder",
                                message=f"Task '{task['task']}' is due in {reminder_minutes} minutes!",
                                timeout=10
                            )
                    except ValueError:
                        continue
            time.sleep(60)  # Check every minute

    def toggle_task_status(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            item_id = selected_item[0]
            task_idx = int(item_id[1:]) - 1

            if self.tasks[task_idx]["status"] == "Pending":
                self.tasks[task_idx]["status"] = "Completed"
            else:
                self.tasks[task_idx]["status"] = "Pending"

            self.save_tasks()
            self.refresh_task_list()
            self.update_calendar_tasks()

    def delete_task(self):
        selected_item = self.tree.selection()
        if selected_item:
            item_id = selected_item[0]
            task_idx = int(item_id[1:]) - 1
            del self.tasks[task_idx]
            self.save_tasks()
            self.refresh_task_list()
            self.update_calendar_tasks()

    def clear_completed(self):
        self.tasks = [task for task in self.tasks if task["status"] != "Completed"]
        self.save_tasks()
        self.refresh_task_list()
        self.update_calendar_tasks()

    def refresh_task_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtered_tasks = self.tasks
        if self.filter_var.get() != "All":
            filtered_tasks = [task for task in self.tasks
                              if task["category"] == self.filter_var.get()]

        for i, task in enumerate(filtered_tasks):
            self.tree.insert("", tk.END, iid=f"I{i + 1}", values=(
                task["task"],
                task["due_date"],
                task["category"],
                task["priority"],
                task["status"]
            ))

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                self.tasks = json.load(f)
        except FileNotFoundError:
            self.tasks = []

    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump(self.tasks, f)

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.tasks_tab = ttk.Frame(self.notebook)
        self.calendar_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.tasks_tab, text="Tasks")
        self.notebook.add(self.calendar_tab, text="Calendar")

        self.create_task_list()
        self.create_calendar_view()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleOrganizer(root)
    root.mainloop()