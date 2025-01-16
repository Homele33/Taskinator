import customtkinter as ctk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta
from tkcalendar import DateEntry, Calendar
import threading
from tktimepicker import SpinTimePickerModern, constants
import time
from plyer import notification
from Task import Task, Subtask


class CTkTimePicker(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Time frame
        time_frame = ctk.CTkFrame(self)
        time_frame.pack(fill="x")

        # Hours
        hour_frame = ctk.CTkFrame(time_frame)
        hour_frame.pack(side="left", padx=5)
        ctk.CTkLabel(hour_frame, text="Hour").pack()
        self.hour_var = ctk.StringVar(value="09")
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
        minute_frame = ctk.CTkFrame(time_frame)
        minute_frame.pack(side="left", padx=5)
        ctk.CTkLabel(minute_frame, text="Minute").pack()
        self.minute_var = ctk.StringVar(value="00")
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
        self.hour_var = ctk.StringVar()
        self.hour_spinbox = ttk.Spinbox(
            self, from_=0, to=23, width=3,
            format="%02.0f",
            textvariable=self.hour_var
        )
        self.hour_spinbox.set("09")
        self.hour_spinbox.pack(side=ctk.LEFT)

        ttk.Label(self, text=":").pack(side=ctk.LEFT)

        # Minute selection
        self.minute_var = ctk.StringVar()
        self.minute_spinbox = ttk.Spinbox(
            self, from_=0, to=59, width=3,
            format="%02.0f",
            textvariable=self.minute_var
        )
        self.minute_spinbox.set("00")
        self.minute_spinbox.pack(side=ctk.LEFT)

    def get_time(self):
        return f"{self.hour_var.get()}:{self.minute_var.get()}"


class NewTaskWindow(ctk.CTkToplevel):
    def __init__(self, parent, categories, callback):
        super().__init__(parent)
        self.callback = callback

        self.title("New Task")
        self.geometry("700x700")
        self.minsize(500, 600)

        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=680)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Task name
        name_frame = ctk.CTkFrame(self.scrollable_frame)
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="Task Name").pack(anchor="w")

        self.task_var = ctk.StringVar()
        ctk.CTkEntry(name_frame, textvariable=self.task_var).pack(fill="x", pady=5)

        # Task description
        desc_frame = ctk.CTkFrame(self.scrollable_frame)
        desc_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(desc_frame, text="Description").pack(anchor="w")

        self.description_text = ctk.CTkTextbox(desc_frame, height=100)
        self.description_text.pack(fill="x", pady=5)

        # Date and time
        datetime_frame = ctk.CTkFrame(self.scrollable_frame)
        datetime_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(datetime_frame, text="Due Date and Time").pack(anchor="w")

        # Date picker (using regular DateEntry as CustomTkinter doesn't have a date picker)
        date_frame = ctk.CTkFrame(datetime_frame)
        date_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(date_frame, text="Date:").pack(side="left")
        self.date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2)
        self.date_picker.pack(side="left", padx=10)

        # Time picker
        time_frame = ctk.CTkFrame(datetime_frame)
        time_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(time_frame, text="Time:").pack(side="left")
        self.time_picker = CTkTimePicker(time_frame)
        self.time_picker.pack(side="left", padx=10)

        # Category and Priority
        details_frame = ctk.CTkFrame(self.scrollable_frame)
        details_frame.pack(fill="x", pady=10)

        # Category
        self.category_var = ctk.StringVar(value="Other")
        ctk.CTkLabel(details_frame, text="Category:").pack(anchor="w")
        ctk.CTkOptionMenu(details_frame, variable=self.category_var,
                          values=categories).pack(fill="x", pady=5)

        # Priority
        self.priority_var = ctk.StringVar(value="Medium")
        ctk.CTkLabel(details_frame, text="Priority:").pack(anchor="w")
        ctk.CTkOptionMenu(details_frame, variable=self.priority_var,
                          values=["High", "Medium", "Low"]).pack(fill="x", pady=5)

        # Subtasks
        subtasks_frame = ctk.CTkFrame(self.scrollable_frame)
        subtasks_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(subtasks_frame, text="Subtasks").pack(anchor="w")

        # Subtask entry
        entry_frame = ctk.CTkFrame(subtasks_frame)
        entry_frame.pack(fill="x", pady=5)

        self.subtask_var = ctk.StringVar()

        ctk.CTkEntry(entry_frame, textvariable=self.subtask_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(entry_frame, text="Add", command=self.add_subtask, width=80).pack(side="right")

        # Subtasks listbox
        self.subtasks_listbox = ctk.CTkCheckBox(subtasks_frame, height=4)
        self.subtasks_listbox.pack(fill="x", pady=5)
        self.subtasks = []

        # Buttons
        btn_frame = ctk.CTkFrame(self.scrollable_frame)
        btn_frame.pack(fill="x", pady=10)

        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy,
                      fg_color="gray").pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Add Task", command=self.submit).pack(side="right", padx=5)

    def add_subtask(self):
        subtask_name = self.subtask_var.get().strip()
        if subtask_name:
            subtask = Subtask(name=subtask_name)
            self.subtasks.append(subtask)
            self.subtasks_listbox.option_add(ctk.END, subtask_name)
            self.subtask_var.set("")

    def submit(self):
        task_name = self.task_var.get().strip()
        description = self.description_text.get("1.0", "end").strip()
        date = self.date_picker.get_date().strftime("%Y-%m-%d")
        time = self.time_picker.get_time()

        if not task_name:
            messagebox.showerror("Error", "Please enter a task name")
            return

        task = Task(
            name=task_name,
            description=description,
            due_date=date,
            due_time=time,
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
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Schedule Organizer")
        self.root.geometry("1200x800")

        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Data storage
        self.tasks : list[Task] = []
        self.categories = ["Work", "Personal", "Study", "Health", "Other"]
        self.load_tasks()

        # # Create main UI
        # self.main_container = ttk.Frame(self.root, padding="10")
        # self.main_container.pack(fill=ctk.BOTH, expand=True)
        self.create_header()
        self.create_tabs()
        self.start_reminder_thread()

    def create_header(self):
        header_frame = ctk.CTkFrame(self.root)
        header_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(header_frame, text="Schedule Organizer",
                     font=("Arial", 24, "bold")).pack(side="left")

        ctk.CTkButton(header_frame, text="New Task",
                      command=self.show_new_task_window).pack(side="right")

    def show_new_task_window(self):
        NewTaskWindow(self.root, self.categories, self.add_task)

    def create_frames(self):
        # Input frame
        self.input_frame = ttk.LabelFrame(self.tasks_tab, text="New Task", padding="10")
        self.input_frame.pack(fill=ctk.X, padx=10, pady=5)

        # List frame
        self.list_frame = ttk.Frame(self.tasks_tab, padding="10")
        self.list_frame.pack(fill=ctk.BOTH, expand=True)

    def create_task_input(self):
        # Task name input
        task_frame = ttk.Frame(self.input_frame)
        task_frame.pack(fill=ctk.X, pady=5)

        ttk.Label(task_frame, text="Task:").pack(side=ctk.LEFT, padx=5)
        self.task_var = ctk.StringVar()
        self.task_entry = ttk.Entry(task_frame, textvariable=self.task_var, width=40)
        self.task_entry.pack(side=ctk.LEFT, padx=5)

        # Date and time selection
        datetime_frame = ttk.Frame(self.input_frame)
        datetime_frame.pack(fill=ctk.X, pady=5)

        ttk.Label(datetime_frame, text="Due Date:").pack(side=ctk.LEFT, padx=5)
        self.date_picker = DateEntry(datetime_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2)
        self.date_picker.pack(side=ctk.LEFT, padx=5)

        ttk.Label(datetime_frame, text="Time:").pack(side=ctk.LEFT, padx=5)
        self.time_picker = TimeEntry(datetime_frame)
        self.time_picker.pack(side=ctk.LEFT, padx=5)

        # Category and priority frame
        cat_pri_frame = ttk.Frame(self.input_frame)
        cat_pri_frame.pack(fill=ctk.X, pady=5)

        # Category selection
        ttk.Label(cat_pri_frame, text="Category:").pack(side=ctk.LEFT, padx=5)
        self.category_var = ctk.StringVar()
        category_combo = ttk.Combobox(cat_pri_frame, textvariable=self.category_var,
                                      values=self.categories, width=10)
        category_combo.pack(side=ctk.LEFT, padx=5)
        category_combo.set("Other")

        # Priority selection
        ttk.Label(cat_pri_frame, text="Priority:").pack(side=ctk.LEFT, padx=5)
        self.priority_var = ctk.StringVar()
        priority_combo = ttk.Combobox(cat_pri_frame, textvariable=self.priority_var,
                                      values=["High", "Medium", "Low"], width=10)
        priority_combo.pack(side=ctk.LEFT, padx=5)
        priority_combo.set("Medium")

        # Reminder frame
        reminder_frame = ttk.Frame(self.input_frame)
        reminder_frame.pack(fill=ctk.X, pady=5)

        ttk.Label(reminder_frame, text="Reminder:").pack(side=ctk.LEFT, padx=5)
        self.reminder_var = ctk.StringVar()
        reminder_combo = ttk.Combobox(reminder_frame, textvariable=self.reminder_var,
                                      values=["5", "15", "30", "60", "120"], width=10)
        reminder_combo.pack(side=ctk.LEFT, padx=5)
        reminder_combo.set("30")
        ttk.Label(reminder_frame, text="minutes before").pack(side=ctk.LEFT, padx=5)

        # Add button
        ttk.Button(reminder_frame, text="Add Task", command=self.add_task).pack(side=ctk.LEFT, padx=20)

    def create_task_list(self):
        # Controls frame
        controls_frame = ctk.CTkFrame(self.tasks_tab)
        controls_frame.pack(fill="x", pady=10)

        # Filter
        ctk.CTkLabel(controls_frame, text="Filter:").pack(side="left", padx=5)
        self.filter_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(controls_frame, variable=self.filter_var,
                          values=["All"] + self.categories,
                          command=self.refresh_task_list).pack(side="left", padx=5)

        # Buttons
        ctk.CTkButton(controls_frame, text="Clear Completed",
                      command=self.clear_completed).pack(side="right", padx=5)
        ctk.CTkButton(controls_frame, text="Delete Selected",
                      command=self.delete_task).pack(side="right", padx=5)

        # Create treeview
        columns = ("Task", "Due Date", "Time", "Category", "Priority", "Status", "Progress")
        self.tree = ttk.Treeview(self.tasks_tab, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        # Scrollbars
        scrollbar = ttk.Scrollbar(self.tasks_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack elements
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind events
        self.tree.bind("<Double-1>", self.toggle_task_status)

        self.refresh_task_list()

    def create_calendar_view(self):
        # Create calendar widget
        self.cal = Calendar(self.calendar_tab, selectmode='day',
                            date_pattern='y-mm-dd')
        self.cal.pack(pady=20, expand=True)

        # Create frame for task list
        self.cal_tasks_frame = ttk.Frame(self.calendar_tab)
        self.cal_tasks_frame.pack(fill=ctk.BOTH, expand=True, pady=10)

        # Create task list for selected date
        columns = ("Time", "Task", "Category", "Priority")
        self.cal_tree = ttk.Treeview(self.cal_tasks_frame, columns=columns, show="headings")

        for col in columns:
            self.cal_tree.heading(col, text=col)
            self.cal_tree.column(col, width=150)

        self.cal_tree.pack(fill=ctk.BOTH, expand=True)

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
            self.cal_tree.insert("", ctk.END, values=(
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
            if(item_id.__contains__("_")):
                parent_id, item_id = item_id.split("_")
                parent_id = int(parent_id[1:])-1
                task_idx = int(item_id[1:])-1
                del self.tasks[parent_id].subtasks[task_idx]
            
            else:
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
            self.tree.insert("", ctk.END, iid=task_id, values=(
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
                self.tree.insert(task_id, ctk.END, iid=subtask_id, values=(
                    f"↳ {subtask.name}",  # Add arrow to show hierarchy
                    "",
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
        # Create tabview
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Add tabs
        self.tasks_tab = self.tabview.add("Tasks")
        self.calendar_tab = self.tabview.add("Calendar")

        self.create_task_list()
        self.create_calendar_view()

    def edit_task(self, task):
        EditTaskWindow(self, self.categories, self.update_task_list, task)

    def update_task_list(self, task, is_new=True):
        if is_new:
            self.tasks.append(task)
        self.refresh_task_list()
        
    

if __name__ == "__main__":
    app = ScheduleOrganizer()
    app.root.mainloop()