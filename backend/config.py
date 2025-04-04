from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

env = os.getenv("FLASK_ENV")
if env == "testing":
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_database.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydatabase.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
