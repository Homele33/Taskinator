from flask import request, jsonify
from config import app, db
from models import Task, SubTask
from sqlalchemy.sql import null
from Ai.taskBreakdown import main as breakdown

from routes import register_blueprints

register_blueprints(app)


@app.route("/api/tasks/status/<int:task_id>", methods=["PATCH"])  # change task status
def toggle_task(task_id):
    task = Task.query.get(task_id)
    status = request.args.get("status")
    if not task:
        return jsonify({"message": "Task not found"}), 404

    task.status = status
    db.session.commit()

    return jsonify({"message": "Task status changed"}), 200


@app.route(
    "/api/task-breaker/<int:task_id>", methods=["GET"]
)  # beak down the task into subtasks using LLM
def breakdown_task(task_id):
    task: Task = Task.query.get(task_id)

    if not task:
        return jsonify({"message": "Task not found"})

    task_break_down, critical_path = breakdown(task.title)

    return jsonify({"message": task_break_down, "critical_path": critical_path})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
