import os
import json
from flask import Blueprint, request, session, jsonify
from sqlalchemy.exc import SQLAlchemyError
from db import db

from src.db.models import Player, Tabelltips26

# Register player and bets
register_bp = Blueprint('register', __name__)
@register_bp.route('/update_user_details', methods=['POST'])
def update_user_details():
    user_id = session.get('user_id')
    if not user_id:
        print("not logged in")
        return jsonify({ 'success': False, 'error': 'not_logged_in' }), 401
    
    player = Player.query.filter_by(id=user_id).first()
    if not player:
        print("User not found:", user_id)
        return jsonify({ 'success': False, 'error': 'user_not_found' }), 404

    data = request.get_json() or {}
    username = data.get('username')
    username_short = data.get('username_short')
    email = data.get('email')
    
    # Update player details
    if len(username) < 3 or len(username_short) < 2:
        return jsonify({"error": "Invalid input"}), 400
    player.username = username
    player.username_short = username_short
    if email is not None and email:
        player.email = email

    try:
        db.session.commit()
        session['username'] = player.username
        session['username_short'] = player.username_short
        session['email'] = player.email
        return jsonify({ 'success': True }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'error': str(e) }), 500

@register_bp.route('/get_tabelltips', methods=['GET'])
def get_tabelltips():
    user_id = session.get('user_id')
    player = Player.query.filter_by(id=user_id).first()
    if not user_id or not player:
        return jsonify({ 'success': False, 'error': 'not_logged_in' }), 401

    # Fetch the team rankings for the current user
    tips = (Tabelltips26.query
            .filter_by(player_id=user_id)
            .order_by(Tabelltips26.rank.asc())
            .all())

    return jsonify([{'team': t.team_name, 'rank': t.rank} for t in tips])


@register_bp.route('/update_rankings', methods=['POST'])
def update_rankings():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({ 'success': False, 'error': 'not_logged_in' }), 401

    data = request.get_json() or {}
    order = data.get('order', [])
    
    if not isinstance(order, list):
        return jsonify({ 'success': False, 'error': 'invalid_payload' }), 400
    
    # Clear old rankings
    Tabelltips26.query.filter_by(player_id=user_id).update(
        {Tabelltips26.rank: None},
        synchronize_session=False
    )
    db.session.flush()

    # Update the rankings in the database
    for rank, team_name in enumerate(order, start=1):
        tabelltips = Tabelltips26.query.filter_by(player_id=user_id, team_name=team_name).first()
        if tabelltips:
            tabelltips.rank = rank
        else:
            new_tabelltips = Tabelltips26(player_id=user_id, team_name=team_name, rank=rank)
            db.session.add(new_tabelltips)

    try:
        db.session.commit()
        return jsonify({ 'success': True }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'error': str(e) }), 500
