import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database - use custom Neon database if available, otherwise use environment DATABASE_URL
custom_database_url = "postgresql://neondb_owner:npg_2wvRQWkasIr9@ep-old-king-a1qaotvu-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
database_url = custom_database_url if custom_database_url else os.environ.get("DATABASE_URL")

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the app with the extension
    db.init_app(app)

    with app.app_context():
        # Make sure to import the models here or their tables won't be created
        import models  # noqa: F401
        db.create_all()

# Configure Flask to properly handle Unicode in JSON responses
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Custom JSON encoder to ensure proper Unicode display
import json
from flask.json.provider import DefaultJSONProvider

class UnicodeJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault('ensure_ascii', False)
        kwargs.setdefault('separators', (',', ':'))
        return json.dumps(obj, **kwargs)

app.json = UnicodeJSONProvider(app)