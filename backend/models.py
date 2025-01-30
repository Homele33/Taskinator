from config import db
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
            "done": self.is_done,
            "description": self.description,
        }
    
class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100),unique=False, nullable=False)
    description = db.Column(db.String(200), nullable=True, unique=False)
    is_done = db.Column(db.Boolean, default=False, nullable=False, unique=False)
    due_date = db.Column(db.Date, nullable=True, unique=False)
    due_time = db.Column(db.Time, nullable=True, unique=False)
    sub_tasks = db.relationship("SubTask", backref="task", lazy=True)
    
    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "done": self.is_done,
            "dueDate": self.due_date,
            "dueTime": self.due_time,
            "subTasks": [sub_task.to_json() for sub_task in self.sub_tasks],

        }

    def add_sub_task(self, sub_task):
        self.sub_tasks.append(sub_task)
        db.session.commit()