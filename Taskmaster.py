import customtkinter as ctk
from Task import Task, Subtask
from TaskList import TaskList


class Taskmaster:
    # Initialize the TaskManager instance.
    def __init__(self):
        # define the root window.
        self.root = ctk.CTk()
        self.root.title("Taskinator")
        self.root.geometry("1200x800")

        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create the main container frame.
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True)

        # Create the header frame.
        self.create_header()

        # Create the tabview to hold the task list and calendar view.
        self.tabview = self.create_tabs()
        self.task_list = TaskList(master=self.tabview.tab("Tasks"))

        # Create a new task entry widget.
        self.new_entry = ctk.CTkEntry(self.main_container, placeholder_text="Enter a new task", )
        self.new_entry.pack(side="bottom", expand=False, fill="x", padx=10)
        self.new_entry.bind("<Return>", lambda event: self.add_task())
        self.new_entry.focus_set()

    def create_header(self):
        # Create the header frame.
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", expand=False)

        header_label = ctk.CTkLabel(header_frame, text="Task Manager", font=("Arial", 24))
        header_label.pack(side="top")

        edit_task_button = ctk.CTkButton(header_frame, text="Edit Task", command=self.edit_task)
        edit_task_button.pack(side="right", padx=10)

    def create_tabs(self):
        # Create a tabview to hold the task list and calendar view.
        tabview = (ctk.CTkTabview(self.main_container))
        tabview.pack(fill="both", expand=True)

        # Create the task list and calendar tabs.
        tabview.add("Tasks")
        tabview.add("Calender")
        return tabview

    def add_task(self):
        # Add a new task to the task list and to the treeview.
        new_task = Task(self.new_entry.get())
        self.task_list.add_task(new_task)
        self.new_entry.delete(0, "end")

    def edit_task(self):
        selected_item = self.task_list.task_tree.treeview.selection()
        print("Selected item: ", selected_item)

    def create_calendar_view(self):
        pass


if __name__ == "__main__":

    app = Taskmaster()
    app.root.mainloop()
