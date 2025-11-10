"""
Authentication routes for user registration, login, logout, and token management
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from email_validator import validate_email, EmailNotValidError
from models import User, UserRepository
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def init_auth_routes(mysql):
    """Initialize authentication routes with database connection"""
    user_repo = UserRepository(mysql)
    
    @auth_bp.route('/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            email = data.get('email', '').strip()
            full_name = data.get('full_name', '').strip()
            password = data.get('password', '')
            
            # Validation
            if not email or not full_name or not password:
                return jsonify({'error': 'Email, full name, and password are required'}), 400
            
            # Validate email format
            try:
                validated_email = validate_email(email)
                email = validated_email.normalized
            except EmailNotValidError as e:
                return jsonify({'error': f'Invalid email: {str(e)}'}), 400
            
            # Validate password strength
            if len(password) < 8:
                return jsonify({'error': 'Password must be at least 8 characters long'}), 400
            
            # Validate full name
            if len(full_name) < 2:
                return jsonify({'error': 'Full name must be at least 2 characters long'}), 400
            
            # Check if email already exists
            if user_repo.email_exists(email):
                return jsonify({'error': 'Email already registered'}), 409
            
            # Create user
            user = user_repo.create_user(email, full_name, password)
            
            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 201
            
        except Exception as e:
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500
    
    @auth_bp.route('/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            if not email or not password:
                return jsonify({'error': 'Email and password are required'}), 400
            
            # Get user by email
            user = user_repo.get_user_by_email(email)
            
            if not user:
                return jsonify({'error': 'Invalid email or password'}), 401
            
            # Verify password
            if not User.verify_password(user.password_hash, password):
                return jsonify({'error': 'Invalid email or password'}), 401
            
            # Generate tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Login failed: {str(e)}'}), 500
    
    @auth_bp.route('/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        try:
            # Get current user identity from refresh token
            current_user_id = get_jwt_identity()
            
            # Create new access token
            access_token = create_access_token(identity=current_user_id)
            
            return jsonify({
                'access_token': access_token
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Token refresh failed: {str(e)}'}), 500
    
    @auth_bp.route('/logout', methods=['POST'])
    @jwt_required()
    def logout():
        try:
            return jsonify({
                'message': 'Logout successful. Please remove tokens from client.'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Logout failed: {str(e)}'}), 500
    
    @auth_bp.route('/verify-token', methods=['GET'])
    @jwt_required()
    def verify_token():
        """Debug endpoint to verify token is working"""
        try:
            current_user_id = get_jwt_identity()
            jwt_data = get_jwt()
            
            return jsonify({
                'message': 'Token is valid',
                'user_id': current_user_id,
                'token_type': jwt_data.get('type', 'access'),
                'expires_at': jwt_data.get('exp', None)
            }), 200
        except Exception as e:
            return jsonify({
                'error': 'Token verification failed',
                'details': str(e)
            }), 401

    return auth_bp