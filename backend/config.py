# config.py
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)

# ---------- CORS ----------
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS = [o.strip() for o in FRONTEND_ORIGINS.split(",") if o.strip()]

CORS(
    app,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
    supports_credentials=True, 
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)

@app.after_request
def add_cors_headers(resp):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    return resp
# -------------------------

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

# ---------- Firebase ----------
FIREBASE_CRED_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./firebase_secret.json")
try:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_app = firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized")
except Exception as e:
    firebase_app = None
    print(f"⚠️ Firebase not initialized: {e}")

def verify_firebase_token(id_token):
    """Verify Firebase ID token and return the corresponding user info."""
    if not firebase_app:
        print("verify_firebase_token called but Firebase is not initialized.")
        return None
    try:
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
        }
    except auth.RevokedIdTokenError:
        return None
    except auth.InvalidIdTokenError:
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None
