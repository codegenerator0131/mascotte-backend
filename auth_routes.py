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
        """
        Register a new user
        
        Expected JSON:
        {
            "email": "user@example.com",
            "full_name": "John Doe",
            "password": "securepassword123"
        }
        """
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
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
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
        """
        Login user and return tokens
        
        Expected JSON:
        {
            "email": "user@example.com",
            "password": "securepassword123"
        }
        """
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
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
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
        """
        Refresh access token using refresh token
        
        Headers:
        Authorization: Bearer <refresh_token>
        """
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
        """
        Logout user
        
        Note: Without token blacklisting, logout is handled client-side by removing tokens.
        This endpoint exists for consistency and can be extended with additional logic.
        
        Headers:
        Authorization: Bearer <access_token>
        """
        try:
            # You can add additional logout logic here if needed
            # For example: logging, analytics, session cleanup, etc.
            
            return jsonify({
                'message': 'Logout successful. Please remove tokens from client.'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Logout failed: {str(e)}'}), 500
    
    @auth_bp.route('/me', methods=['GET'])
    @jwt_required()
    def get_current_user():
        """
        Get current user information
        
        Headers:
        Authorization: Bearer <access_token>
        """
        try:
            # Get current user
            current_user_id = get_jwt_identity()
            user = user_repo.get_user_by_id(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'user': user.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get user: {str(e)}'}), 500
    
    @auth_bp.route('/change-password', methods=['POST'])
    @jwt_required()
    def change_password():
        """
        Change user password
        
        Headers:
        Authorization: Bearer <access_token>
        
        Expected JSON:
        {
            "old_password": "oldpassword123",
            "new_password": "newpassword123"
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            
            if not old_password or not new_password:
                return jsonify({'error': 'Old password and new password are required'}), 400
            
            # Validate new password strength
            if len(new_password) < 8:
                return jsonify({'error': 'New password must be at least 8 characters long'}), 400
            
            # Get current user
            current_user_id = get_jwt_identity()
            user = user_repo.get_user_by_id(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Verify old password
            if not User.verify_password(user.password_hash, old_password):
                return jsonify({'error': 'Old password is incorrect'}), 401
            
            # Update password
            new_password_hash = User.hash_password(new_password)
            user_repo.update_user(current_user_id, password_hash=new_password_hash)
            
            return jsonify({
                'message': 'Password changed successfully'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Password change failed: {str(e)}'}), 500
    
    return auth_bp