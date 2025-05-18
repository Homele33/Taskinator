from flask import Blueprint, request, jsonify, g
from config import db
from models import SubTask, Task
from services.auth_middleware import auth_required

subtasks_bp = Blueprint("subtasks", __name__)


@subtasks_bp.route("/<int:task_id>", methods=["POST"])  # add a subtask to a task
@auth_required
def add_subtask(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    if not task:
        return jsonify({"message": "Task not found"}), 404

    data = request.json
    sub_task = SubTask(title=data.get("title"), description=data.get("description"))
    task.add_sub_task(sub_task)

    return jsonify({"message": "Subtask added"}), 201


@subtasks_bp.route(
    "/<int:task_id>/<int:subtask_id>", methods=["DELETE"]
)  # delete a subtask
@auth_required
def delete_subtask(task_id, subtask_id):
    subtask = SubTask.query.filter_by(task_id=task_id, id=subtask_id).first()

    if not subtask:
        return jsonify({"message": "subtask not found"}), 404
    db.session.delete(subtask)
    db.session.commit()

    return jsonify({"message": "Subtask deleted"}), 200


@subtasks_bp.route(
    "/<int:task_id>/<int:subtask_id>", methods=["PATCH"]
)  # toggle a subtask
@auth_required
def toggle_subtask(task_id, subtask_id):
    subtask = SubTask.query.filter_by(task_id=task_id, id=subtask_id).first()

    if not subtask:
        return jsonify({"message": "Task or subtask not found"}), 404

    subtask.is_done = not subtask.is_done
    db.session.commit()

    return jsonify({"message": "Subtask toggled"}), 200


@subtasks_bp.route("/<int:task_id>", methods=["GET"])
@auth_required
# get all subtasks of a task
def get_subtasks(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()

    # in case we dont find the taks
    if not task:
        return jsonify({"message": "Task Not Found"}), 404
    return jsonify([sub_task.to_json() for sub_task in task.sub_tasks])
