from flask import Blueprint, request, jsonify
from services.nlp import parse_task_text

task_nlp_bp = Blueprint("task_nlp", __name__)


@task_nlp_bp.route("/parse-task", methods=["POST"])
def parse_task():
    data = request.get_json()
    data = data["text"]
    parsed_task = parse_task_text(data)
    return jsonify(parsed_task)
