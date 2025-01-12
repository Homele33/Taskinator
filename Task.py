import json
from datetime import datetime

class Subtask:
    def __init__(self,name: str, priority):
        self.name : str = name
        self.priority = priority
        self.is_completed : bool = False
    
    def toggle_completed(self) -> None:
        self.is_completed = not self.is_completed
    


class Task(Subtask):
    def __init__(self, name: str, description: str, due_date, due_time, category, priority):
        # Initialize a new Task instance.
        self.name = name
        self.description = description
        self.due_date = due_date
        self.due_time = due_time
        self.is_completed = False
        self.category = category
        self.priority = priority
        self.subtasks: Subtask = []
        self.completed_subtasks = 0
        self.total_subtasks = 0
        self.remaining_subtasks = 0 
        self.completed_subtasks_percentage = 0
    
    def calculate_subtask_percentages(self) -> None:
        if self.total_subtasks > 0:
            self.completed_subtasks_percentage = (self.completed_subtasks / self.total_subtasks) * 100
        else:
            self.completed_subtasks_percentage = 0

    def add_subtask(self, subtask: Subtask) -> None:
        self.subtasks.append(subtask)
        self.total_subtasks += 1
        if subtask.is_completed:
            self.completed_subtasks += 1
        self.remaining_subtasks = self.total_subtasks - self.completed_subtasks
        self.calculate_subtask_percentages()


    def update_task_details(self, name=None, description=None, due_date=None, due_time=None, category=None, priority=None):
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if due_date is not None:
            self.due_date = due_date
        if due_time is not None:
            self.due_time = due_time
        if category is not None:
            self.category = category
        if priority is not None:
            self.priority = priority
    

    def get_task_summary(self):
        return {
            "name": self.name,
            "description": self.description,
            "due_date": self.due_date,
            "due_time": self.due_time,
            "completed": self.is_completed,
            "category": self.category,
            "priority": self.priority,
            "total_subtasks": self.total_subtasks,
            "completed_subtasks": self.completed_subtasks,
            "remaining_subtasks": self.remaining_subtasks,
            "completed_subtasks_percentage": self.completed_subtasks_percentage
        }
    

    def mark_subtask_as_completed(self, subtask_name):
        for subtask in self.subtasks:
            if subtask.name == subtask_name:
                subtask.mark_as_completed()
                self.completed_subtasks += 1
                self.remaining_subtasks -= 1
                self.calculate_subtask_percentages()
                break


    def list_subtasks(self):
        return [subtask.name for subtask in self.subtasks]


    def find_subtask_by_name(self, subtask_name):
        for subtask in self.subtasks:
            if subtask.name == subtask_name:
                return subtask
        return None


    def remove_subtask(self, subtask_name):
        subtask_to_remove = self.find_subtask_by_name(subtask_name)
        if subtask_to_remove:
            self.subtasks.remove(subtask_to_remove)
            self.total_subtasks -= 1
            if subtask_to_remove.completed:
                self.completed_subtasks -= 1
            self.remaining_subtasks = self.total_subtasks - self.completed_subtasks
            self.calculate_subtask_percentages()

    def to_dict(self):
        #  return the task as a dictionary
        return {
            "name": self.name,
            "description": self.description,
            "due_date": self.due_date,
            "due_time": self.due_time,
            "completed": self.is_completed,
            "category": self.category,
            "priority": self.priority,
            "total_subtasks": self.total_subtasks,
            "completed_subtasks": self.completed_subtasks,
            "remaining_subtasks": self.remaining_subtasks,
            "completed_subtasks_percentage": self.completed_subtasks_percentage,
            "subtasks": [subtask.to_dict() for subtask in self.subtasks] if self.subtasks else [],
        }

    @classmethod
    def from_json(cls, data):
        task = cls(
            name=data["name"],
            description=data["description"],
            due_date=data["due_date"],
            due_time=data["due_time"],
            category=data["category"],
            priority=data["priority"]
        )
        task.is_completed = data["completed"]
        task.completed_subtasks = data["completed_subtasks"]
        task.total_subtasks = data["total_subtasks"]
        task.remaining_subtasks = data["remaining_subtasks"]
        task.completed_subtasks_percentage = data["completed_subtasks_percentage"]
        
        # Recursively create subtasks
        for subtask_data in data["subtasks"]:
            subtask = cls.from_json(subtask_data)
            task.add_subtask(subtask)
        
        return task