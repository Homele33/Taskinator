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
    return jsonify({"tasks": json_tasks}), 200


@tasks_bp.route("", methods=["POST"])
@auth_required
# create a task
def create_task():
    title = request.json.get("title")
    task_type = request.json.get("task_type")
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
        task_type=task_type,
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
    task.task_type = data.get("task_type", task.task_type)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)
    task.priority = data.get("priority", task.priority)
    due_date = data.get("dueDate")
    if due_date != "" and due_date:
        task.due_date = datetime.fromisoformat(due_date)
    else:
        task.due_date = null()
    try:
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 401

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
    try:
        db.session.delete(task)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 401

    return jsonify({"message": "Task deleted"}), 200


@tasks_bp.route("/<int:task_id>", methods=["GET"])  # get a single task
@auth_required
def get_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    if not task:
        return jsonify({"message": "Task not found"}), 404

    return jsonify(task.to_json()), 200


@tasks_bp.route("/<int:task_id>", methods=["PUT"])  # change task status
@auth_required
def toggle_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    status = request.json

    if not task:
        return jsonify({"message": "Task not found"}), 404

    try:
        task.status = status
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 401

    return jsonify({"message": "Task status changed"}), 200
