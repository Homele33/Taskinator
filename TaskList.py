import json
from Task import Task
from TaskTreeview import TaskTreeview

class TaskList:
    # TaskList class to manage tasks
    def __init__(self, master):
        # create the task treeview
        self.task_tree = TaskTreeview(master)
        # define the categories and priorities
        self.categories = ["Personal", "Work", "School", "Home"]
        self.priorities = ["High", "Medium", "Low"]

        # load in tasks
        self.tasks = self.load_tasks()
        self.task_tree.load_tasks(self.tasks)

    def add_task(self, task: Task):
        # add a new task to the treeview
        self.tasks.append(task)
        self.task_tree.add_task(task)
        self.save_tasks()

    def load_tasks(self):
        # load in tasks from the tasks.json file
        try:
            with open("tasks.json", "r") as file:
                tasks_data = json.load(file)
                self.tasks = [Task.from_json(task) for task in tasks_data]
                return self.tasks
        except FileNotFoundError:
            return []

    def save_tasks(self):
        # save the tasks to the tasks.json file
        with open("tasks.json", "w") as file:
            json.dump([task.to_dict() for task in self.tasks], file, indent=4)