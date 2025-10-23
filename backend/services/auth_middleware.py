# backend/services/auth_middleware.py
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime
from config import verify_firebase_token
from models import User, db


def auth_required(f):
    """Require Firebase auth for API routes. Let CORS preflight pass cleanly."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Allow CORS preflight without auth
        if request.method == "OPTIONS":
            # Don't call the endpoint function here; just acknowledge preflight.
            return ("", 204)

        # Extract Bearer token
        auth_header = (request.headers.get("Authorization") or "").strip()
        prefix = "Bearer "
        if not auth_header or not auth_header.startswith(prefix):
            return jsonify({"message": "Authorization token is missing or invalid"}), 401

        id_token = auth_header[len(prefix):].strip()
        if not id_token:
            return jsonify({"message": "Authorization token is missing or invalid"}), 401

        # Verify token with Firebase
        user_info = verify_firebase_token(id_token)
        if not user_info:
            return jsonify({"message": "Invalid or expired token"}), 401

        # Ensure user exists in local DB
        uid = user_info.get("uid")
        email = user_info.get("email")
        display_name = user_info.get("name")
        photo_url = user_info.get("picture")

        # Fallback for users without email (phone-only auth, etc.)
        if not email:
            email = f"{uid}@firebase.local"

        user = User.query.filter_by(firebase_uid=uid).first()
        if not user:
            user = User(
                firebase_uid=uid,
                email=email,
                display_name=display_name,
                photo_url=photo_url,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()

        # Make user available downstream
        g.user = user

        return f(*args, **kwargs)

    return wrapper
