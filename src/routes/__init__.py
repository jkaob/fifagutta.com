from flask import Blueprint
from .auth import auth_bp
from .register import register_bp
from .bets import bets_bp, matches_bp

def register_blueprints(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(register_bp, url_prefix='/register')
    app.register_blueprint(bets_bp, url_prefix='/bets')
    app.register_blueprint(matches_bp, url_prefix='/matches')