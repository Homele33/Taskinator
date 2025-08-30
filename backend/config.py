from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Accept", "Origin", "Authorization"],
            "supports_credentials": True,
        }
    },
)


IN_DOCKER = os.path.exists("/.dockerenv")

if IN_DOCKER:
    try:
        os.makedirs("/instance", exist_ok=True)
    except Exception as e:
        print(f"Warning: could not ensure /instance dir: {e}")

db_url = os.getenv("DATABASE_URL")  

if db_url:
    if db_url.startswith("sqlite:///instance/"):
        if IN_DOCKER:
            db_url = "sqlite:////instance/" + db_url.split("sqlite:///instance/", 1)[1]
        else:
            local_instance = os.path.join(os.path.dirname(__file__), "instance")
            os.makedirs(local_instance, exist_ok=True)
            rel = db_url.split("sqlite:///instance/", 1)[1]
            db_url = "sqlite:///" + os.path.join(local_instance, rel).replace("\\", "/")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
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
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        picture = decoded_token.get("picture")
        return {"uid": uid, "email": email, "name": name, "picture": picture}
    except auth.RevokedIdTokenError:
        return None
    except auth.InvalidIdTokenError:
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None
