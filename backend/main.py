from flask import request, jsonify
from config import app, db
from models import Task, SubTask

@app.route("/api/tasks", methods=["GET"])# get all tasks
def get_tasks():
    tasks = Task.query.all()
    json_tasks = list(map(lambda x: x.to_json(), tasks))
    return jsonify({"tasks": json_tasks})

@app.route("/api/task/<int:task_id>", methods=["GET"]) # get a single task
def get_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"message": "Task not found"}), 404
    
    return jsonify(task.to_json())

@app.route("/api/task/<int:task_id>/subtasks", methods=["GET"]) # get all subtasks of a task
def get_subtasks(task_id):
    task = Task.query.get(task_id)
    return jsonify([sub_task.to_json() for sub_task in task.sub_tasks])

@app.route("/api/create_task", methods=["POST"]) # create a task
def create_task():
    title = request.json.get("title")
    description = request.json.get("description")
    due_date = request.json.get("dueDate")
    due_time = request.json.get("dueTime")
    sub_tasks = request.json.get("subTasks")
    
    if not title:
        return jsonify({"message": "You must include a title"}), 400

    new_task = Task(
        title=title, description=description, due_date=due_date, due_time=due_time
    )
    
    # subtasks handling
    new_task.sub_tasks = [SubTask(title=sub_task["title"], description=sub_task.get("description")) for sub_task in sub_tasks]

    try:
        # add to data base
        db.session.add(new_task)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    # return success message
    return jsonify({"message": "Task created!"}), 201

@app.route("/api/add_subtask/<int:task_id>",methods=["POST"]) # add a subtask to a task
def add_subtask(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"message": "Task not found"}), 404

    data = request.json
    sub_task = SubTask(title=data.get("title"), description=data.get("description"))
    task.add_sub_task(sub_task)

    return jsonify({"message": "Subtask added"}), 201

@app.route("/api/update_task/<int:task_id>", methods=["PATCH"]) # update a task
def update_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"message": "Task Not Found"}), 404

    data = request.json
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.due_date = data.get("dueDate", task.due_date)
    task.due_time = data.get("dueTime", task.due_time)

    db.session.commit()

    return jsonify({"message": "Task updated"}), 200

@app.route("/api/delete_task/<int:task_id>", methods=["DELETE"]) # delete a task
def delete_task(task_id):
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({"message": "Task not found"}), 404
    
    for subtask in task.sub_tasks:
        db.session.delete(subtask)

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"}), 200

@app.route("/api/delete_subtask/<int:task_id>/<int:subtask_id>", methods=["DELETE"]) # delete a subtask
def delete_subtask(task_id, subtask_id):
    task = Task.query.get(task_id)
    subtask = SubTask.query.get(subtask_id)

    if not task or not subtask:
        return jsonify({"message": "Task or subtask not found"}), 404

    db.session.delete(subtask)
    db.session.commit()

    return jsonify({"message": "Subtask deleted"}), 200

@app.route("/api/toggle_task/<int:task_id>", methods=["PATCH"]) # toggle a task
def toggle_task(task_id):
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({"message": "Task not found"}), 404

    task.is_done = not task.is_done
    db.session.commit()

    return jsonify({"message": "Task toggled"}), 200

@app.route("/api/toggle_subtask/<int:task_id>/<int:subtask_id>", methods=["PATCH"]) # toggle a subtask
def toggle_subtask(task_id, subtask_id):
    task = Task.query.get(task_id)
    subtask = SubTask.query.get(subtask_id)

    if not task or not subtask:
        return jsonify({"message": "Task or subtask not found"}), 404
    
    subtask.is_done = not subtask.is_done
    db.session.commit()

    return jsonify({"message": "Subtask toggled"}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)