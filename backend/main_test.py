import unittest
from unittest.mock import patch, MagicMock
from datetime import time
from config import db, app
from models import User, UserPreferences
from Ai.network.inference import initialize_bn_for_user

app.testing = True
client = app.test_client()


class TestFlaskAPI(unittest.TestCase):
    """
    Updated tests for Bayesian Network integration.
    
    The new BN system requires:
    1. User authentication (mocked here)
    2. UserPreferences created before tasks
    3. BN initialization before task creation
    """
    
    def setUp(self):
        """Set up test database and create test user with preferences."""
        with app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(
                id=999,
                firebase_uid="test_firebase_uid_123",
                email="test@example.com",
                display_name="Test User"
            )
            db.session.add(self.test_user)
            db.session.commit()
            
            # Create preferences for test user
            self.test_prefs = UserPreferences(
                user_id=self.test_user.id,
                days_off=["Saturday", "Sunday"],
                workday_pref_start=time(9, 0),
                workday_pref_end=time(17, 0),
                focus_peak_start=time(10, 0),
                focus_peak_end=time(12, 0),
                default_duration_minutes=60,
                deadline_behavior="ON_TIME",
                flexibility="MEDIUM"
            )
            db.session.add(self.test_prefs)
            db.session.commit()
            
            # Initialize BN for test user
            initialize_bn_for_user(self.test_user.id)

    def tearDown(self):
        """Clean up test database."""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    @patch('services.auth_middleware.auth_required')
    def test_create_task_with_bn(self, mock_auth):
        """Test creating a task with BN system initialized."""
        # Mock authentication to return test user
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                from flask import g
                g.user = self.test_user
                return f(*args, **kwargs)
            wrapper.__name__ = f.__name__
            return wrapper
        mock_auth.side_effect = mock_decorator
        
        with app.app_context():
            response = client.post(
                "/api/tasks",
                json={
                    "title": "Test Task with BN",
                    "description": "Testing BN integration",
                    "dueDate": "2025-07-23",
                    "durationMinutes": 60,
                },
            )
            # Should succeed now that BN is trained
            self.assertEqual(response.status_code, 201)
            self.assertIn("message", response.json)

    @patch('services.auth_middleware.auth_required')
    def test_get_tasks(self, mock_auth):
        """Test retrieving tasks."""
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                from flask import g
                g.user = self.test_user
                return f(*args, **kwargs)
            wrapper.__name__ = f.__name__
            return wrapper
        mock_auth.side_effect = mock_decorator
        
        with app.app_context():
            response = client.get("/api/tasks")
            self.assertEqual(response.status_code, 200)

    @patch('services.auth_middleware.auth_required')
    def test_update_task_with_bn(self, mock_auth):
        """Test updating a task with BN learning."""
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                from flask import g
                g.user = self.test_user
                return f(*args, **kwargs)
            wrapper.__name__ = f.__name__
            return wrapper
        mock_auth.side_effect = mock_decorator
        
        with app.app_context():
            # First create a task
            create_response = client.post(
                "/api/tasks",
                json={
                    "title": "Initial Task",
                    "description": "Task before update",
                    "dueDate": "2025-07-23",
                    "durationMinutes": 60,
                },
            )
            self.assertEqual(create_response.status_code, 201)
            task_id = create_response.json.get("id")
            
            # Then update it
            response = client.patch(
                f"/api/tasks/{task_id}",
                json={
                    "title": "Updated Task",
                    "description": "Task after update",
                    "dueDate": "2025-08-01",
                },
            )
            self.assertEqual(response.status_code, 200)
            
    def test_task_creation_fails_without_bn(self):
        """Test that task creation is blocked without BN training."""
        # Create a user without preferences/BN
        with app.app_context():
            new_user = User(
                id=888,
                firebase_uid="test_no_bn_uid",
                email="no_bn@example.com",
                display_name="No BN User"
            )
            db.session.add(new_user)
            db.session.commit()
            
            with patch('services.auth_middleware.auth_required') as mock_auth:
                def mock_decorator(f):
                    def wrapper(*args, **kwargs):
                        from flask import g
                        g.user = new_user
                        return f(*args, **kwargs)
                    wrapper.__name__ = f.__name__
                    return wrapper
                mock_auth.side_effect = mock_decorator
                
                response = client.post(
                    "/api/tasks",
                    json={
                        "title": "Should Fail",
                        "description": "No BN trained",
                        "dueDate": "2025-07-23",
                    },
                )
                # Should return 403 Forbidden
                self.assertEqual(response.status_code, 403)
                self.assertIn("preferences", response.json.get("message", "").lower())


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    unittest.main()
