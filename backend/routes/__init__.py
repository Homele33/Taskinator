# from flask import Blueprint
from .task_nlp import task_nlp_bp


def register_blueprints(app):
    app.register_blueprint(task_nlp_bp, url_prefix="/ai")
