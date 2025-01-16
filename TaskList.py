import customtkinter as ctk
import tkinter as tk
from Task import Task
from tkinter import ttk

# class TaskList(ctk.CTkScrollableFrame):
#     def __init__(self, master, title, values):
#         super().__init__(master,label_text=title)
#         self.title = title
#         self.values = values
#         self.grid_columnconfigure(0, weight=1)
#         self.tasks = []
#
#         for i, value in enumerate(self.values):
#             task =  ctk.CTkCheckBox(self, text=value)
#             task.grid(row=i, column=0, sticky="w")
#             self.tasks.append(task)
#
#     def get_selected_tasks(self):
#         selected_tasks = []
#         for task in self.tasks:
#             if task.get() == 1:
#                 selected_tasks.append(task.cget("text"))
#         return selected_tasks


class TaskFrame(ctk.CTkFrame):
    def __init__(self, master, tasks):
        super().__init__(master)
        self.master = master
        self.tasks = tasks

        # treeview customization
        background_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        # define the style
        tree_style = ttk.Style()
        tree_style.theme_use("default")
        tree_style.configure("Treeview", background=background_color, fieldbackground=background_color, foreground=text_color)
        tree_style.map("Treeview", background=[('selected', selected_color)])
        self.bind("<<TreeviewSelect>>", lambda event: self.focus_get())


        # treeview widget data
        self.treeview = ttk.Treeview(master = self.master, show="tree")
        self.treeview.pack(fill="both", expand=True)

        # load in tasks
        for i, task in enumerate(self.tasks):
            task_id = self.treeview.insert("","end", text=task.name)
            if task.subtasks:
                for j, subtask in enumerate(task.subtasks):
                    self.treeview.insert(task_id, j, f'{task_id}s{j}', text=subtask.name)

    def add_task(self, task: Task):
        # add a new task to the treeview
        self.tasks.append(task)
        task_id = self.treeview.insert("", "end", text=task.name)
        for sub_task in task.subtasks:
            self.treeview.insert(task_id, "end", text=sub_task.name)