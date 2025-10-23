from .subtasks import subtasks_bp
from .tasks import tasks_bp
from .preferences import preferences_bp
from .ai import ai_bp

def register_blueprints(app):
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(subtasks_bp, url_prefix="/api/tasks/subtasks")
    app.register_blueprint(preferences_bp, url_prefix="/api/preferences")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    