from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)

# Configure CORS to allow requests from frontend
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Accept", "Origin", "Authorization"],
            "supports_credentials": True,
        }
    },
)



env = os.getenv("FLASK_ENV")


if env == "testing":
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_database.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

cred = credentials.Certificate("./firebase_secret.json")
firebase_app = firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token):
    """
    Verify Firebase ID token and return the corresponding user info
    """
    try:
        # Verify the ID token while checking if the token is revoked
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        # Get user info from decoded token
        uid = decoded_token["uid"]
        # Additional claims from token if needed
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        picture = decoded_token.get("picture")

        return {"uid": uid, "email": email, "name": name, "picture": picture}
    except auth.RevokedIdTokenError:
        # Token has been revoked
        return None
    except auth.InvalidIdTokenError:
        # Token is invalid
        return None
    except Exception as e:
        # Other errors
        print(f"Error verifying token: {e}")
        return None
