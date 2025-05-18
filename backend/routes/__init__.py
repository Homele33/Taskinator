from .task_nlp import task_nlp_bp
from .subtasks import subtasks_bp
from .tasks import tasks_bp
from .user_preferences import preferences_bp


def register_blueprints(app):
    app.register_blueprint(task_nlp_bp, url_prefix="/api/ai")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(subtasks_bp, url_prefix="/api/tasks/subtasks")
    app.register_blueprint(preferences_bp, url_prefix="/api/preferences")
