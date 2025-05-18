from datetime import datetime
from flask import jsonify
from config import db
from models import Task


def create_task(title, description=None, due_date=None):
    if due_date:
        due_date = datetime.fromisoformat(due_date)
    new_task = Task(
        title=title,
        task_type="Meeting",
        description=description,
        due_date=due_date,
        status="TODO",
        priority="MEDIUM",
    )
    try:
        db.session.add(new_task)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)})

    return jsonify({"message": "task created"})
