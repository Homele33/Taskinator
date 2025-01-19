import customtkinter as ctk
from tkinter import ttk

class TaskTreeview(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master = master)
        self.master = master

        # treeview customization
        background_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        # define the style
        tree_style = ttk.Style()
        tree_style.theme_use("default")
        tree_style.configure("Treeview", background=background_color, fieldbackground=background_color,
                             foreground=text_color)
        tree_style.map("Treeview", background=[('selected', selected_color)])
        self.bind("<<TreeviewSelect>>", lambda event: self.focus_get())

        # treeview widget data
        self.treeview = ttk.Treeview(master=self.master, show="tree")
        self.treeview.pack(fill="both", expand=True)

    def load_tasks(self, tasks):
        # load in tasks and subtasks to the treeview
        for i, task in enumerate(tasks):
            task_id = self.treeview.insert("", "end", text=task.name)
            if task.subtasks:
                for j, subtask in enumerate(task.subtasks):
                    self.treeview.insert(task_id, j, f'{task_id}s{j}', text=subtask.name)

    def add_task(self, task):
        # add a new task to the treeview
        task_id = self.treeview.insert("", "end", text=task.name)
        for sub_task in task.subtasks:
            self.treeview.insert(task_id, "end", text=sub_task.name)