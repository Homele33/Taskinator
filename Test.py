import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta
import os
from tkcalendar import DateEntry, Calendar
import threading
from tktimepicker import SpinTimePickerModern, constants
import time
from plyer import notification
from Task import Task

class TimePicker(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Time frame
        time_frame = ttk.Frame(self)
        time_frame.pack(fill=tk.X)
        
        # Hours
        hour_frame = ttk.Frame(time_frame)
        hour_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(hour_frame, text="Hour").pack()
        self.hour_var = tk.StringVar(value="09")
        self.hour_spinbox = ttk.Spinbox(
            hour_frame,
            from_=0,
            to=23,
            width=2,
            format="%02.0f",
            textvariable=self.hour_var,
            wrap=True
        )
        self.hour_spinbox.pack()
        
        # Minutes
        minute_frame = ttk.Frame(time_frame)
        minute_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(minute_frame, text="Minute").pack()
        self.minute_var = tk.StringVar(value="00")
        self.minute_spinbox = ttk.Spinbox(
            minute_frame,
            from_=0,
            to=59,
            width=2,
            format="%02.0f",
            textvariable=self.minute_var,
            wrap=True,
            increment=5
        )
        self.minute_spinbox.pack()
        
    def get_time(self):
        return f"{self.hour_var.get()}:{self.minute_var.get()}"

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
        self.geometry("700x700")
        self.minsize(500, 600)
        
        # Make window modal
        self.transient(parent)
        self.grab_set()
        
        # Create scrollable canvas
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Task name
        name_frame = ttk.LabelFrame(main_frame, text="Task Name", padding="10")
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.task_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.task_var).pack(fill=tk.X)
        
        # Task description
        desc_frame = ttk.LabelFrame(main_frame, text="Description", padding="10")
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.description_text = tk.Text(desc_frame, height=4)
        self.description_text.pack(fill=tk.X)
        
        # Date and time
        datetime_frame = ttk.LabelFrame(main_frame, text="Due Date and Time", padding="10")
        datetime_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Date picker
        date_frame = ttk.Frame(datetime_frame)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT, padx=(0, 10))
        self.date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                   foreground='white', borderwidth=2)
        self.date_picker.pack(side=tk.LEFT)
        
        # Time picker
        time_frame = ttk.Frame(datetime_frame)
        time_frame.pack(fill=tk.X, pady=5)
        ttk.Label(time_frame, text="Time:").pack(side=tk.LEFT, padx=(0, 10))
        self.time_picker = TimePicker(time_frame)
        self.time_picker.pack(side=tk.LEFT)
        
        # Category and Priority
        details_frame = ttk.LabelFrame(main_frame, text="Task Details", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Category
        cat_frame = ttk.Frame(details_frame)
        cat_frame.pack(fill=tk.X, pady=5)
        ttk.Label(cat_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 10))
        self.category_var = tk.StringVar(value="Other")
        ttk.Combobox(cat_frame, textvariable=self.category_var,
                    values=categories, width=15).pack(side=tk.LEFT)
        
        # Priority
        pri_frame = ttk.Frame(details_frame)
        pri_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pri_frame, text="Priority:").pack(side=tk.LEFT, padx=(0, 10))
        self.priority_var = tk.StringVar(value="Medium")
        ttk.Combobox(pri_frame, textvariable=self.priority_var,
                    values=["High", "Medium", "Low"], width=15).pack(side=tk.LEFT)
        
        # Subtasks
        subtasks_frame = ttk.LabelFrame(main_frame, text="Subtasks", padding="10")
        subtasks_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Subtask entry
        entry_frame = ttk.Frame(subtasks_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        self.subtask_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.subtask_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(entry_frame, text="Add", command=self.add_subtask, width=10).pack(side=tk.LEFT)
        
        # Subtasks listbox with scrollbar
        listbox_frame = ttk.Frame(subtasks_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.subtasks_listbox = tk.Listbox(listbox_frame, height=4)
        subtask_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.subtasks_listbox.yview)
        self.subtasks_listbox.configure(yscrollcommand=subtask_scrollbar.set)
        
        self.subtasks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        subtask_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.subtasks = []
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Add Task", command=self.submit, width=10).pack(side=tk.RIGHT, padx=5)
        
        # Pack the canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure canvas scrolling
        self.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Center the window
        self.center_window()
        
    def add_subtask(self):
        subtask_name = self.subtask_var.get().strip()
        if subtask_name:
            subtask = Task(
                name=subtask_name,
                description="",
                due_date="",
                due_time="",
                category="",
                priority="Low"
            )
            self.subtasks.append(subtask)
            self.subtasks_listbox.insert(tk.END, subtask_name)
            self.subtask_var.set("")
        
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
    def submit(self):
        task_name = self.task_var.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
        
        # Get date in correct format
        date = self.date_picker.get_date().strftime("%Y-%m-%d")
        
        # Get time in correct format
        time = self.time_picker.get_time()
        
        if not task_name:
            messagebox.showerror("Error", "Please enter a task name", parent=self)
            return
        
        # Create new Task instance with separate date and time
        task = Task(
            name=task_name,
            description=description,
            due_date=date,  # Pass date separately
            due_time=time,  # Pass time separately
            category=self.category_var.get(),
            priority=self.priority_var.get()
        )
        
        for subtask in self.subtasks:
            task.add_subtask(subtask)
        
        self.callback(task)
        self.destroy()

class EditTaskWindow(NewTaskWindow):
    def __init__(self, parent, categories, callback, task):
        super().__init__(parent, categories, callback)
        self.title("Edit Task")
        self.task = task
        self.populate_fields()

    def populate_fields(self):
        # Populate the fields with existing task data
        self.task_name.set(self.task.name)
        self.date_picker.set_date(datetime.strptime(self.task.due_date, '%Y-%m-%d').date())
        self.time_picker.set_time(self.task.due_time)
        self.category_var.set(self.task.category)
        self.priority_var.set(self.task.priority)

    def submit(self):
        # Override submit to update existing task instead of creating new one
        name = self.task_name.get()
        due_date = self.date_picker.get_date().strftime('%Y-%m-%d')
        due_time = self.time_picker.get_time()
        category = self.category_var.get()
        priority = self.priority_var.get()

        self.task.update_task_details(
            name=name,
            due_date=due_date, 
            due_time=due_time,
            category=category,
            priority=priority
        )
        
        self.callback(self.task, is_new=False)
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
        self.tasks :Task = []
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
        list_container = ttk.Frame(self.tasks_tab, padding="10")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Controls frame
        controls_frame = ttk.Frame(list_container)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filter
        ttk.Label(controls_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.filter_var,
                                  values=["All"] + self.categories, width=15)
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.set("All")
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_task_list())
        
        # Buttons
        ttk.Button(controls_frame, text="Delete Selected",
                  command=self.delete_task).pack(side=tk.RIGHT, padx=5)
        ttk.Button(controls_frame, text="Clear Completed",
                  command=self.clear_completed).pack(side=tk.RIGHT, padx=5)
        
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(list_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with show="tree headings" to show hierarchy
        columns = ("Task", "Description", "Due Date", "Time", "Category", "Priority", "Status", "Progress")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")
        
        # Set column headings and widths
        widths = {
            "Task": 100,
            "Description": 200,
            "Due Date": 100,
            "Time": 80,
            "Category": 100,
            "Priority": 80,
            "Status": 80,
            "Progress": 100
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths.get(col, 150))
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack elements
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.toggle_task_status)
        
        # Load existing tasks
        self.refresh_task_list()
        
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
        day_tasks = [task for task in self.tasks if task.due_date == selected_date]
        
        # Sort by time
        day_tasks.sort(key=lambda x: x.due_time)
        
        # Add tasks to tree
        for task in day_tasks:
            self.cal_tree.insert("", tk.END, values=(
                task.due_time,
                task.name,
                task.category,
                task.priority
            ))

    def add_task(self, task: Task):
        try:
            # Validate date and time separately
            datetime.strptime(task.due_date, "%Y-%m-%d")
            datetime.strptime(task.due_time, "%H:%M")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date or time format: {str(e)}")
            return
            
        self.tasks.append(task)
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
                # Use dot notation
                if task.status == "Pending" and task.due_date:
                    try:
                        due_time = datetime.strptime(task.due_date, "%Y-%m-%d %H:%M")
                        reminder_minutes = int(task.reminder)
                        reminder_time = due_time - timedelta(minutes=reminder_minutes)

                        if current_time >= reminder_time and current_time < reminder_time + timedelta(minutes=1):
                            notification.notify(
                                title="Task Reminder",
                                message=f"Task '{task.name}' is due in {reminder_minutes} minutes!",
                                timeout=10
                            )
                    except ValueError:
                        continue
            time.sleep(60)

    def toggle_task_status(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            item_id = selected_item[0]
            if(item_id.__contains__("_")):
                parent_id, item_id = item_id.split("_")
                parent_id = int(parent_id[1:])-1
                task_idx = int(item_id[1:])-1
                self.tasks[parent_id].subtasks[task_idx].toggle_completed()
                self.tasks[parent_id].calculate_subtask_percentages()
            else:
                task_idx = int(item_id[1:]) - 1
                self.tasks[task_idx].toggle_completed()

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
        self.tasks = [task for task in self.tasks if not task.is_completed]
        self.save_tasks()
        self.refresh_task_list()
        self.update_calendar_tasks()

    def refresh_task_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        filtered_tasks = self.tasks
        if self.filter_var.get() != "All":
            filtered_tasks = [task for task in self.tasks 
                            if task.category == self.filter_var.get()]
            
        for i, task in enumerate(filtered_tasks):
            progress = f"{task.completed_subtasks_percentage:.1f}%" if task.total_subtasks > 0 else "N/A"
            task_id = f"I{i+1}"
            
            # Insert main task
            self.tree.insert("", tk.END, iid=task_id, values=(
                task.name,
                task.description[:50] + "..." if len(task.description) > 50 else task.description,
                task.due_date,
                task.due_time,
                task.category,
                task.priority,
                "Completed" if task.is_completed else "Pending",
                progress
            ))
            
            # Insert subtasks
            for j, subtask in enumerate(task.subtasks):
                subtask_id = f"{task_id}_S{j+1}"
                self.tree.insert(task_id, tk.END, iid=subtask_id, values=(
                    f"↳ {subtask.name}",  # Add arrow to show hierarchy
                    subtask.description[:50] + "..." if len(subtask.description) > 50 else subtask.description,
                    "",  # No due date for subtasks
                    "",  # No time for subtasks
                    "",  # No category for subtasks
                    "",  # No priority for subtasks
                    "Completed" if subtask.is_completed else "Pending",
                    ""   # No progress for subtasks
                ))

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                task_data = json.load(f)
                self.tasks = [Task.from_json(data) for data in task_data]
        except FileNotFoundError:
            self.tasks = []

    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump([task.to_dict() for task in self.tasks], f)

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.tasks_tab = ttk.Frame(self.notebook)
        self.calendar_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.tasks_tab, text="Tasks")
        self.notebook.add(self.calendar_tab, text="Calendar")

        self.create_task_list()
        self.create_calendar_view()

    def edit_task(self, task):
        EditTaskWindow(self, self.categories, self.update_task_list, task)

    def update_task_list(self, task, is_new=True):
        if is_new:
            self.tasks.append(task)
        self.refresh_task_list()
        
    

if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleOrganizer(root)
    root.mainloop()