# backend/models.py
from datetime import datetime
from config import db


class User(db.Model):
    """User model that links to Firebase authentication"""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)

    # Use callables for timestamps (evaluated at row insert/update time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    tasks = db.relationship(
        "Task",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    # Optional: quick backref to preferences (one-to-one)
    preferences = db.relationship(
        "UserPreferences",
        uselist=False,
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
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
    __tablename__ = "sub_task"

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

    # Named enums (future-proof for Postgres)
    task_type = db.Column(
        db.Enum("Meeting", "Training", "Studies", name="task_type_enum"),
        nullable=True,
    )
    description = db.Column(db.String(200), nullable=True, unique=False)
    is_done = db.Column(db.Boolean, default=False, nullable=False, unique=False)

    # Legacy fields still in use on UI
    due_date = db.Column(db.DateTime, nullable=True, unique=False)
    due_time = db.Column(db.Time, nullable=True, unique=False)

    sub_tasks = db.relationship(
        "SubTask", backref="task", lazy=True, cascade="all, delete-orphan"
    )

    priority = db.Column(
        db.Enum("LOW", "MEDIUM", "HIGH", name="priority_enum"),
        nullable=True,
    )
    status = db.Column(
        db.Enum("TODO", "IN_PROGRESS", "COMPLETED", name="status_enum"),
        nullable=True,
    )

    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Scheduling fields used by suggestions/AI
    scheduled_start = db.Column(db.DateTime, nullable=True, index=True)
    scheduled_end = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        # speeds up: "all tasks of a user ordered by start" queries
        db.Index("ix_task_user_start", "user_id", "scheduled_start"),
    )

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "task_type": self.task_type,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "dueDate": self.due_date.isoformat() if self.due_date else None,
            "dueTime": self.due_time.isoformat() if self.due_time else None,
            "durationMinutes": self.duration_minutes,
            "subtasks": [sub_task.to_json() for sub_task in self.sub_tasks],
            "userId": self.user_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "scheduledStart": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "scheduledEnd": self.scheduled_end.isoformat() if self.scheduled_end else None,
        }

    def add_sub_task(self, sub_task):
        self.sub_tasks.append(sub_task)
        db.session.commit()


class UserPreferences(db.Model):
    """Prior/preferences that the suggestor uses."""
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True
    )

    # days_off: list[int]  0..6 (Sun..Sat) per המימוש שלנו
    days_off = db.Column(db.JSON, nullable=False, default=list)

    workday_pref_start = db.Column(db.Time, nullable=True)
    workday_pref_end = db.Column(db.Time, nullable=True)
    focus_peak_start = db.Column(db.Time, nullable=True)
    focus_peak_end = db.Column(db.Time, nullable=True)

    default_duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    deadline_behavior = db.Column(
        db.Enum("EARLY", "ON_TIME", "LAST_MINUTE", name="deadline_behavior_enum"),
        nullable=True,
    )
    flexibility = db.Column(
        db.Enum("LOW", "MEDIUM", "HIGH", name="flexibility_enum"),
        nullable=True,
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_json(self):
        return {
            "userId": self.user_id,
            "daysOff": self.days_off,
            "workdayPrefStart": self.workday_pref_start.isoformat() if self.workday_pref_start else None,
            "workdayPrefEnd": self.workday_pref_end.isoformat() if self.workday_pref_end else None,
            "focusPeakStart": self.focus_peak_start.isoformat() if self.focus_peak_start else None,
            "focusPeakEnd": self.focus_peak_end.isoformat() if self.focus_peak_end else None,
            "defaultDurationMinutes": self.default_duration_minutes,
            "deadlineBehavior": self.deadline_behavior,
            "flexibility": self.flexibility,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
