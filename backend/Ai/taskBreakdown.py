import ollama
import json
from typing import Dict


class TaskBreakdown:
    def __init__(self, model_name: str = "llama3.2"):
        """
        Initialize the TaskBreakdown class with a specific ollama model.

        Args:
            model_name (str): Name of ollama model to use. default is "llama3.2".

        """
        self.model_name = model_name

    def _create_prompt(self, task: str) -> str:
        """
         Create a structured prompt for the LLM to break down tasks.

        Args:
            task (str): The main task to break down

        Returns:
            str: Formatted prompt for the LLM
        """
        return f"""Break down the following task into detailed subtasks.
        format the response as a JSON with the following structure:
        {{
            "main_task": "task description",
            "subtasks": [
            {{
                "id": "1",
                "title": "subtask title",
                "description": "subtask description",
                "dependencies" ["ids of dependent subtasks"],
            }}
            ]

        }}

        Task to break down : {task}

        Provide only the JSON response without any additional text.
        """

    def break_down_task(self, task: str) -> Dict:
        """
        break down tasks using the model

        Args:
            task(str): the main task to break.

        Returns:
            Dict: JSON object containing the main task with the subtasks
        """

        try:
            prompt = self._create_prompt(task)

            response = ollama.generate(
                model=self.model_name, prompt=prompt, stream=False
            )

            result = json.loads(response["response"])
            return result
        except json.JSONDecodeError as error:
            raise ValueError(f"Failed to parse LLM response as JSON {error}")
        except Exception as error:
            raise Exception(f"Error breaking down task")

    def get_critical_path(self, breakdown: Dict) -> list[str]:
        """ """

        # Create dependencies graph
        graph = {}
        for subtask in breakdown["subtasks"]:
            graph[subtask["id"]] = subtask["dependencies"]

        def find_path(task_id: str, visited: set):
            if task_id in visited:
                return []
            visited.add(task_id)

            max_path = [task_id]

            for dependent in graph[task_id]:
                path = find_path(dependent, visited)
                if len(path) > len(max_path) - 1:
                    max_path = [task_id] + path
            return max_path

        critical_path = []
        for task_id in graph:
            path = find_path(task_id, set())
            if len(path) > len(critical_path):
                critical_path = path
        return critical_path


def main(task):
    task_system = TaskBreakdown()

    try:
        breakdown = task_system.break_down_task(task)

        critical_path = task_system.get_critical_path(breakdown)

        return [breakdown, critical_path]

    except Exception as error:
        print(f"Error: {error}")
