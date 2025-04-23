import unittest
from config import db
from main import app
from routes import register_blueprints

app.testing = True

client = app.test_client()


class TestFlaskAPI(unittest.TestCase):
    def setUp(self):
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_task(self):
        response = client.post(
            "/api/tasks",
            json={
                "title": "Test Task",
                "description": "This is a test task",
                "dueDate": "2025-07-23",
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_get_tasks(self):
        response = client.get("/api/tasks")
        self.assertEqual(response.status_code, 200)

    def test_update_task(self):
        """Test updating a task after creation"""
        # First create a task
        create_response = client.post(
            "/api/tasks",
            json={
                "title": "Initial Task",
                "description": "This is an initial task",
                "dueDate": "2025-07-23",
            },
        )
        id = create_response.json["id"]
        # Then update it
        response = client.patch(
            f"/api/tasks/{id}",
            json={
                "title": "Updated task",
                "description": "This is a test for updating task",
                "dueDate": "2025-01-01",
            },
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    unittest.main()
