from config import db
from datetime import datetime


class User(db.Model):
    """User model that links to Firebase authentication"""

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    last_login = db.Column(db.DateTime, nullable=True)
    tasks = db.relationship(
        "Task", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def to_json(self):
        return {
            "id": self.id,
            "email": self.email,
            "displayName": self.display_name,
            "photoUrl": self.photo_url,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastLogin": self.last_login.isoformat() if self.last_login else None,
        }


class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=False)
    is_done = db.Column(db.Boolean, default=False, nullable=False, unique=False)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    description = db.Column(db.String(200), nullable=True, unique=False)

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "isDone": self.is_done,
            "description": self.description,
        }


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    description = db.Column(db.String(200), nullable=True, unique=False)
    is_done = db.Column(db.Boolean, default=False, nullable=False, unique=False)
    due_date = db.Column(db.DateTime, nullable=True, unique=False)
    due_time = db.Column(db.Time, nullable=True, unique=False)
    sub_tasks = db.relationship(
        "SubTask", backref="task", lazy=True, cascade="all, delete-orphan"
    )
    priority = db.Column(db.Enum("LOW", "MEDIUM", "HIGH"))
    status = db.Column(db.Enum("TODO", "IN_PROGRESS", "COMPLETED"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "dueDate": self.due_date.isoformat() if self.due_date else None,
            "dueTime": self.due_time.isoformat() if self.due_time else None,
            "subtasks": [sub_task.to_json() for sub_task in self.sub_tasks],
            "userId": self.user_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def add_sub_task(self, sub_task):
        self.sub_tasks.append(sub_task)
        db.session.commit()
