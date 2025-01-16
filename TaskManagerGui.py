import customtkinter as ctk
from Task import Task, Subtask
from TaskList import TaskFrame
from icecream import ic

class TaskManagerGui:
    # Initialize the TaskManager instance.
    def __init__(self):
        # define the root window.
        self.root = ctk.CTk()
        self.root.title("Taskinator")
        self.root.geometry("1200x800")
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # todo : move task data organization to a separate class
        self.tasks = [Task("Task 1"), Task("Task 2"), Task("Task 3")]
        self.tasks[0].add_subtask(Subtask("Subtask 1"))
        self.tasks[0].add_subtask(Subtask("Subtask 2"))
        self.tasks[1].subtasks.append(Subtask("Subtask 3"))
        self.categories = ["Personal", "Work", "School", "Home"]
        self.priorities = ["High", "Medium", "Low"]

        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True)


        self.create_header()
        self.create_tabs()

        self.new_entry = ctk.CTkEntry(self.main_container, placeholder_text="Enter a new task", )
        self.new_entry.pack(side="bottom", expand=False, fill="x", padx=10)
        self.new_entry.bind("<Return>", lambda event: self.add_task())
        # self.new_entry.grid(row=0, column=0, sticky='W', padx=10, columnspan=2)




    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", expand=False)

        header_label = ctk.CTkLabel(header_frame, text="Task Manager", font=("Arial", 24))
        header_label.pack(side="top")

        edit_task_button = ctk.CTkButton(header_frame, text="Edit Task", command=self.edit_task)
        edit_task_button.pack(side="right", padx=10)

    def create_tabs(self):
        # Create a tabview to hold the task list and calendar view.
        self.tabview = (ctk.CTkTabview(self.main_container))
        self.tabview.pack(fill="both", expand=True)
        # self.tabview.grid(row=0, column=0, sticky="nsew")
        # Create the task list and calendar tabs.
        self.task_tabs = self.tabview.add("Tasks")
        self.calender_tab = self.tabview.add("Calender")

        self.create_task_list()
        self.create_calendar_view()

    def add_task(self):
        new_task = Task(self.new_entry.get())
        ic(new_task.name)
        self.tasks.append(new_task)
        self.task_list_frame.add_task(new_task)
        self.new_entry.delete(0, "end")
        # self.reload_task_list()


    def edit_task(self):
        selected_item = self.task_list_frame.treeview.selection()
        print("Selected item: ", selected_item)

    def create_task_list(self):
        # Create a grid to hold the task list.
        self.task_list_frame = TaskFrame(master=self.task_tabs,tasks=self.tasks)


    def create_calendar_view(self):
        pass


if __name__ == "__main__":

    app = TaskManagerGui()
    app.root.mainloop()
