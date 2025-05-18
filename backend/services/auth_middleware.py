from functools import wraps
from flask import request, jsonify, g
from config import verify_firebase_token
from models import User, db
from datetime import datetime


def auth_required(f):
    """
    Decorator to require authentication for API routes
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the auth token from the request header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token is missing or invalid"}), 401

        # Extract the token from the header
        token = auth_header.split("Bearer ")[1]

        # Verify the token
        user_info = verify_firebase_token(token)
        if not user_info:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Look for the user in our database
        user = User.query.filter_by(firebase_uid=user_info["uid"]).first()

        # If user doesn't exist, create them
        if not user:
            user = User(
                firebase_uid=user_info["uid"],
                email=user_info["email"],
                display_name=user_info.get("name"),
                photo_url=user_info.get("picture"),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()

        # Make the user object available to the view function
        g.user = user

        return f(*args, **kwargs)

    return decorated_function
