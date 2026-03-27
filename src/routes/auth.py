import os
import json
from flask import Blueprint, json, request, session, jsonify, redirect, url_for

from ..db.models import Player

PASSWORD_ID = json.loads(os.getenv('FIFAGUTTA_PASSWORDS_ID_JSON'))


# Login / Register name / register bets
auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/login', methods=['POST'])
def login():
    print("attempting login")
    data = request.get_json() or {}
    pw = data.get('password', '')
    user_id = PASSWORD_ID.get(pw)
    if not user_id:
        print("invalid password:", pw)
        return jsonify({'success': False}), 401
    
    player = Player.query.filter_by(id=user_id).first()
    if not player:
        print("User not found:", user_id)
        return jsonify({'success': False, 'error': 'user_not_found'}), 404
    
    session['user_id'] = player.id
    session['full_name'] = player.full_name
    session['username'] = player.username
    session['username_short'] = player.username_short
    session['screen_name'] = player.username if player.username else player.full_name
    session['email'] = player.email

    return jsonify({
        'success': True, 
        'user_id': player.id, 
        'full_name': player.full_name,
        'username': player.username, 
        'username_short': player.username_short,
        'email': player.email}), 200

# Logout route
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for("index"))
