import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy() # ORM handle
migrate = Migrate() # ties into Alembic under the hood

DB_URI = os.getenv('FIFAGUTTA_DATABASE_URL')

### INITIALIZATION

def init_db(app):
    # Binds SQLAlchemy and Flask-Migrate to the Flask app.
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', DB_URI)
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    db.init_app(app)
    with app.app_context():
        db.create_all()   # ← creates all tables defined by your models
    migrate.init_app(app, db)