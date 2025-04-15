# from flask import Blueprint
from .task_nlp import task_nlp_bp
from .subtasks import subtasks_bp
from .tasks import tasks_bp


def register_blueprints(app):
    app.register_blueprint(task_nlp_bp, url_prefix="/ai")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(subtasks_bp, url_prefix="/api/tasks/subtasks")
