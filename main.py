import Task


import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
import json

# Define the file to save tasks
data_file = "tasks.json"

def load_tasks():
    try:
        with open(data_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_tasks(tasks):
    with open(data_file, "w") as file:
        json.dump(tasks, file)

def add_task():
    task_name = task_entry.get()
    due_date = date_picker.get_date()
    due_time = time_entry.get()
    if task_name.strip() == "":
        messagebox.showwarning("Input Error", "Task name cannot be empty!")
        return

    tasks.append({"name": task_name, "subtasks": [], "completed": False, "due_date": str(due_date), "due_time": due_time})
    save_tasks(tasks)
    update_task_list()
    task_entry.delete(0, tk.END)
    time_entry.delete(0, tk.END)

def update_task_list():
    task_list.delete(0, tk.END)
    today = datetime.now().date()
    for idx, task in enumerate(tasks):
        status = "[Done]" if task["completed"] else "[Pending]"
        due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
        if due_date == today:
            due_date_display = "(Due: Today)"
        elif due_date == today.replace(day=today.day + 1):
            due_date_display = "(Due: Tomorrow)"
        else:
            due_date_display = f"(Due: {task['due_date']})"
        due_time_display = f"{task['due_time']}" if "due_time" in task else ""
        task_list.insert(tk.END, f"{idx + 1}. {task['name']} {status} {due_date_display} {due_time_display}")
        for sub_idx, subtask in enumerate(task["subtasks"]):
            sub_status = "[Done]" if subtask["completed"] else "[Pending]"
            sub_due_date = datetime.strptime(subtask["due_date"], "%Y-%m-%d").date()
            if sub_due_date == today:
                sub_due_date_display = "(Due: Today)"
            elif sub_due_date == today.replace(day=today.day + 1):
                sub_due_date_display = "(Due: Tomorrow)"
            else:
                sub_due_date_display = f"(Due: {subtask['due_date']})"
            sub_due_time_display = f"{subtask['due_time']}" if "due_time" in subtask else ""
            task_list.insert(tk.END, f"    {sub_idx + 1}. {subtask['name']} {sub_status} {sub_due_date_display} {sub_due_time_display}")

def mark_task_done():
    selected = task_list.curselection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a task to mark as done!")
        return

    selected_index = selected[0]
    for idx, task in enumerate(tasks):
        if selected_index == 0:
            task["completed"] = True
            save_tasks(tasks)
            update_task_list()
            return
        selected_index -= 1
        for subtask in task["subtasks"]:
            if selected_index == 0:
                subtask["completed"] = True
                save_tasks(tasks)
                update_task_list()
                return
            selected_index -= 1

def delete_task():
    selected = task_list.curselection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a task to delete!")
        return

    selected_index = selected[0]
    for idx, task in enumerate(tasks):
        if selected_index == 0:
            del tasks[idx]
            save_tasks(tasks)
            update_task_list()
            return
        selected_index -= 1
        for sub_idx, _ in enumerate(task["subtasks"]):
            if selected_index == 0:
                del task["subtasks"][sub_idx]
                save_tasks(tasks)
                update_task_list()
                return
            selected_index -= 1

def edit_task():
    selected = task_list.curselection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a task to edit!")
        return

    selected_index = selected[0]
    for idx, task in enumerate(tasks):
        if selected_index == 0:
            TaskEditor(idx)
            return
        selected_index -= 1
        for sub_idx, _ in enumerate(task["subtasks"]):
            if selected_index == 0:
                SubtaskEditor(idx, sub_idx)
                return
            selected_index -= 1

def manage_subtasks():
    selected = task_list.curselection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a task to manage subtasks!")
        return

    selected_index = selected[0]
    for idx, task in enumerate(tasks):
        if selected_index == 0:
            SubtaskManager(idx)
            return
        selected_index -= 1
        for _ in task["subtasks"]:
            selected_index -= 1

class SubtaskManager:
    def __init__(self, task_index):
        self.task_index = task_index
        self.task = tasks[task_index]

        self.window = tk.Toplevel()
        self.window.title(f"Subtasks for: {self.task['name']}")

        self.subtask_list = tk.Listbox(self.window, width=50, height=15)
        self.subtask_list.pack(pady=10)
        self.update_subtask_list()

        entry_frame = tk.Frame(self.window)
        entry_frame.pack(pady=5)

        self.subtask_entry = tk.Entry(entry_frame, width=20)
        self.subtask_entry.pack(side=tk.LEFT, padx=5)

        self.subtask_date_picker = DateEntry(entry_frame, width=10)
        self.subtask_date_picker.pack(side=tk.LEFT, padx=5)

        self.subtask_time_entry = tk.Entry(entry_frame, width=8)
        self.subtask_time_entry.insert(0, "HH:MM")
        self.subtask_time_entry.pack(side=tk.LEFT, padx=5)

        add_subtask_button = tk.Button(entry_frame, text="Add Subtask", command=self.add_subtask)
        add_subtask_button.pack(side=tk.LEFT, padx=5)

        action_frame = tk.Frame(self.window)
        action_frame.pack(pady=10)

        mark_done_button = tk.Button(action_frame, text="Mark Subtask as Done", command=self.mark_subtask_done)
        mark_done_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(action_frame, text="Delete Subtask", command=self.delete_subtask)
        delete_button.pack(side=tk.LEFT, padx=5)

        edit_button = tk.Button(action_frame, text="Edit Subtask", command=self.edit_subtask)
        edit_button.pack(side=tk.LEFT, padx=5)

    def update_subtask_list(self):
        self.subtask_list.delete(0, tk.END)
        today = datetime.now().date()
        for idx, subtask in enumerate(self.task["subtasks"]):
            status = "[Done]" if subtask["completed"] else "[Pending]"
            sub_due_date = datetime.strptime(subtask["due_date"], "%Y-%m-%d").date()
            if sub_due_date == today:
                sub_due_date_display = "(Due: Today)"
            elif sub_due_date == today.replace(day=today.day + 1):
                sub_due_date_display = "(Due: Tomorrow)"
            else:
                sub_due_date_display = f"(Due: {subtask['due_date']})"
            sub_due_time_display = f"{subtask['due_time']}" if "due_time" in subtask else ""
            self.subtask_list.insert(tk.END, f"{idx + 1}. {subtask['name']} {status} {sub_due_date_display} {sub_due_time_display}")

    def add_subtask(self):
        subtask_name = self.subtask_entry.get()
        subtask_due_date = self.subtask_date_picker.get_date()
        subtask_due_time = self.subtask_time_entry.get()
        if subtask_name.strip() == "":
            messagebox.showwarning("Input Error", "Subtask name cannot be empty!")
            return

        self.task["subtasks"].append({"name": subtask_name, "completed": False, "due_date": str(subtask_due_date), "due_time": subtask_due_time})
        save_tasks(tasks)
        self.update_subtask_list()
        self.subtask_entry.delete(0, tk.END)
        self.subtask_time_entry.delete(0, tk.END)

    def mark_subtask_done(self):
        selected = self.subtask_list.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a subtask to mark as done!")
            return

        subtask_index = selected[0]
        self.task["subtasks"][subtask_index]["completed"] = True
        save_tasks(tasks)
        self.update_subtask_list()

    def delete_subtask(self):
        selected = self.subtask_list.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a subtask to delete!")
            return

        subtask_index = selected[0]
        del self.task["subtasks"][subtask_index]
        save_tasks(tasks)
        self.update_subtask_list()

    def edit_subtask(self):
        selected = self.subtask_list.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a subtask to edit!")
            return

        subtask_index = selected[0]
        SubtaskEditor(self.task_index, subtask_index)

class TaskEditor:
    def __init__(self, task_index):
        self.task_index = task_index
        self.task = tasks[task_index]

        self.window = tk.Toplevel()
        self.window.title("Edit Task")

        tk.Label(self.window, text="Task Name:").pack(pady=5)
        self.task_name_entry = tk.Entry(self.window, width=30)
        self.task_name_entry.insert(0, self.task["name"])
        self.task_name_entry.pack(pady=5)

        tk.Label(self.window, text="Due Date:").pack(pady=5)
        self.task_date_picker = DateEntry(self.window)
        self.task_date_picker.set_date(self.task["due_date"])
        self.task_date_picker.pack(pady=5)

        tk.Label(self.window, text="Due Time:").pack(pady=5)
        self.task_time_entry = tk.Entry(self.window, width=10)
        self.task_time_entry.insert(0, self.task["due_time"])
        self.task_time_entry.pack(pady=5)

        save_button = tk.Button(self.window, text="Save Changes", command=self.save_changes)
        save_button.pack(pady=10)

    def save_changes(self):
        self.task["name"] = self.task_name_entry.get()
        self.task["due_date"] = str(self.task_date_picker.get_date())
        self.task["due_time"] = self.task_time_entry.get()
        save_tasks(tasks)
        update_task_list()
        self.window.destroy()

class SubtaskEditor:
    def __init__(self, task_index, subtask_index):
        self.task_index = task_index
        self.task = tasks[task_index]
        self.subtask = self.task["subtasks"][subtask_index]

        self.window = tk.Toplevel()
        self.window.title("Edit Subtask")

        tk.Label(self.window, text="Subtask Name:").pack(pady=5)
        self.subtask_name_entry = tk.Entry(self.window, width=30)
        self.subtask_name_entry.insert(0, self.subtask["name"])
        self.subtask_name_entry.pack(pady=5)

        tk.Label(self.window, text="Due Date:").pack(pady=5)
        self.subtask_date_picker = DateEntry(self.window)
        self.subtask_date_picker.set_date(self.subtask["due_date"])
        self.subtask_date_picker.pack(pady=5)

        tk.Label(self.window, text="Due Time:").pack(pady=5)
        self.subtask_time_entry = tk.Entry(self.window, width=10)
        self.subtask_time_entry.insert(0, self.subtask["due_time"])
        self.subtask_time_entry.pack(pady=5)

        save_button = tk.Button(self.window, text="Save Changes", command=self.save_changes)
        save_button.pack(pady=10)

    def save_changes(self):
        self.subtask["name"] = self.subtask_name_entry.get()
        self.subtask["due_date"] = str(self.subtask_date_picker.get_date())
        self.subtask["due_time"] = self.subtask_time_entry.get()
        save_tasks(tasks)
        update_task_list()
        self.window.destroy()

# Load existing tasks
tasks = load_tasks()

# Create the main window
root = tk.Tk()
root.title("To-Do List App")

frame_top = tk.Frame(root)
frame_top.pack(pady=10)

task_entry = tk.Entry(frame_top, width=20)
task_entry.pack(side=tk.LEFT, padx=5)

date_picker = DateEntry(frame_top, width=10)
date_picker.pack(side=tk.LEFT, padx=5)

time_entry = tk.Entry(frame_top, width=8)
time_entry.insert(0, "HH:MM")
time_entry.pack(side=tk.LEFT, padx=5)

add_task_button = tk.Button(frame_top, text="Add Task", command=add_task)
add_task_button.pack(side=tk.LEFT, padx=5)

frame_middle = tk.Frame(root)
frame_middle.pack(pady=10)

scrollbar = tk.Scrollbar(frame_middle)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

task_list = tk.Listbox(frame_middle, width=50, height=15, yscrollcommand=scrollbar.set)
task_list.pack(side=tk.LEFT)

scrollbar.config(command=task_list.yview)

frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=10)

mark_done_button = tk.Button(frame_bottom, text="Mark as Done", command=mark_task_done)
mark_done_button.pack(side=tk.LEFT, padx=5)

delete_button = tk.Button(frame_bottom, text="Delete Task", command=delete_task)
delete_button.pack(side=tk.LEFT, padx=5)

edit_button = tk.Button(frame_bottom, text="Edit Task", command=edit_task)
edit_button.pack(side=tk.LEFT, padx=5)

subtask_button = tk.Button(frame_bottom, text="Manage Subtasks", command=manage_subtasks)
subtask_button.pack(side=tk.LEFT, padx=5)

update_task_list()

root.mainloop()
