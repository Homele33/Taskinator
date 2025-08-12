from flask import jsonify, g
from config import app, db
from models import Task, SubTask
from services.auth_middleware import auth_required

from routes import register_blueprints
from flask_migrate import Migrate

migrate = Migrate(app, db)
register_blueprints(app)


@app.route("/health", methods=["GET"])
def cheack_health():
    return {"status": "ok"}, 200


@app.route("/api/auth-test", methods=["GET"])
@auth_required
def auth_test():
    return jsonify({"message": "Authentication successful", "user": g.user.to_json()})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
