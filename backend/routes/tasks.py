from flask import Blueprint, request, jsonify, g
from models import Task, SubTask
from datetime import datetime
from config import db
from sqlalchemy.sql import null

from services import auth_middleware
from services.auth_middleware import auth_required

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("", methods=["GET"])
@auth_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=g.user.id).all()
    json_tasks = list(map(lambda x: x.to_json(), tasks))
    return jsonify({"tasks": json_tasks})


@tasks_bp.route("", methods=["POST"])
@auth_required
# create a task
def create_task():
    title = request.json.get("title")
    description = request.json.get("description")
    due_date = request.json.get("dueDate")
    if due_date:
        due_date = datetime.fromisoformat(due_date)
    due_time = request.json.get("dueTime")
    sub_tasks = request.json.get("subTasks")
    priority = request.json.get("priority")
    status = request.json.get("status")
    user_id = g.user.id
    if not title:
        return jsonify({"message": "You must include a title"}), 400

    new_task = Task(
        title=title,
        description=description,
        due_date=due_date,
        due_time=due_time,
        status=status,
        priority=priority,
        user_id=user_id,
    )

    # subtasks handling
    if sub_tasks:
        new_task.sub_tasks = [
            SubTask(title=sub_task["title"], description=sub_task.get("description"))
            for sub_task in sub_tasks
        ]

    try:
        # add to data base
        db.session.add(new_task)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    # return success message
    return jsonify({"message": "Task created!", "id": new_task.id}), 201


@tasks_bp.route("/<int:task_id>", methods=["PATCH"])
@auth_required
# update a task
def update_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    if not task:
        return jsonify({"message": "Task Not Found"}), 404

    data = request.json
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)

    due_date = data.get("dueDate")
    if due_date != "" and due_date:
        task.due_date = date.fromisoformat(due_date)
    else:
        task.due_date = null()

    db.session.commit()

    return jsonify({"message": "Task updated"}), 200


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@auth_required
# delete a task
def delete_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    if not task:
        return jsonify({"message": "Task not found"}), 404

    # for subtask in task.sub_tasks:
    # db.session.delete(subtask)

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"}), 200


@tasks_bp.route("/<int:task_id>", methods=["GET"])  # get a single task
@auth_required
def get_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    if not task:
        return jsonify({"message": "Task not found"}), 404

    return jsonify(task.to_json())


@tasks_bp.route("/status/<int:task_id>", methods=["PATCH"])  # change task status
@auth_required
def toggle_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    status = request.args.get("status")

    if not task:
        return jsonify({"message": "Task not found"}), 404

    task.status = status
    db.session.commit()

    return jsonify({"message": "Task status changed"}), 200
