from flask import Blueprint, request, jsonify
from services.nlp import parse_task_text
from services.task_creation import create_task

task_nlp_bp = Blueprint("task_nlp", __name__)


@task_nlp_bp.route("/parseTask", methods=["POST"])
def parse_task():
    data = request.get_json()
    data = data["text"]
    parsed_task = parse_task_text(data)
    if not parsed_task["title"]:
        return jsonify({"massage": "Error creating task: no title found"}), 400
    title = parsed_task["title"]
    res = create_task(title=title, description=None, due_date=parsed_task["due_date"])
    return res, 201
