"""
Avatar routes for avatar setup, profile management, and related operations
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from avatar_models import (
    AvatarRepository, BodyMeasurementRepository, 
    AvatarGarmentRepository
)

avatar_bp = Blueprint('avatar', __name__, url_prefix='/api/avatar')


def init_avatar_routes(mysql):
    """Initialize avatar routes with database connection"""
    avatar_repo = AvatarRepository(mysql)
    measurements_repo = BodyMeasurementRepository(mysql)
    garments_repo = AvatarGarmentRepository(mysql)
    
    @avatar_bp.route('/setup', methods=['POST'])
    @jwt_required()
    def setup_avatar():
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate required fields
            required_fields = ['fullName', 'age', 'height', 'heightUnit', 
                             'weight', 'weightUnit', 'avatarType', 'measurementMode']
            
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'{field} is required'}), 400
            
            # Validate avatar type specific requirements
            if data['avatarType'] == 'generic' and not data.get('genericAvatarStyle'):
                return jsonify({'error': 'Generic avatar style is required'}), 400
            
            if data['avatarType'] == 'biometric' and not data.get('biometricVerified'):
                return jsonify({'error': 'Biometric verification is required'}), 400
            
            # Check if avatar already exists for user
            existing_avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            if existing_avatar:
                return jsonify({'error': 'Avatar already exists for this user'}), 409
            
            # Prepare avatar data
            avatar_data = {
                'full_name': data['fullName'],
                'bio': data.get('bio', ''),
                'age': data['age'],
                'height': data['height'],
                'height_unit': data['heightUnit'],
                'weight': data['weight'],
                'weight_unit': data['weightUnit'],
                'avatar_type': data['avatarType'],
                'generic_avatar_style': data.get('genericAvatarStyle'),
                'biometric_verified': data.get('biometricVerified', False),
                'measurement_mode': data['measurementMode'],
                'auto_estimated': data.get('autoEstimated', False),
                'share_with_world': data.get('shareWithWorld', False),
                'create_assistant': data.get('createAssistant', False),
                'create_greeting_cards': data.get('createGreetingCards', False),
                'public_profile': data.get('publicProfile', False),
                'allow_connections': data.get('allowConnections', True),
                'selected_greeting_template': data.get('selectedGreetingTemplate')
            }
            
            # Create avatar
            avatar = avatar_repo.create_avatar(current_user_id, avatar_data)
            
            # Create body measurements
            body_measurements = data.get('bodyMeasurements', {})
            if body_measurements:
                measurements_data = {
                    'chest': body_measurements.get('chest'),
                    'waist': body_measurements.get('waist'),
                    'hips': body_measurements.get('hips'),
                    'shoulder_width': body_measurements.get('shoulderWidth'),
                    'inseam': body_measurements.get('inseam'),
                    'arm_length': body_measurements.get('armLength'),
                    'neck_size': body_measurements.get('neckSize')
                }
                measurements = measurements_repo.create_measurements(avatar.id, measurements_data)
            else:
                measurements = None
            
            # Add selected garments
            selected_garments = data.get('selectedGarments', [])
            for garment_id in selected_garments:
                garments_repo.add_garment(avatar.id, garment_id)
            
            # Get complete avatar data
            avatar_response = avatar.to_dict()
            if measurements:
                avatar_response['bodyMeasurements'] = measurements.to_dict()
            
            avatar_response['selectedGarments'] = selected_garments
            
            return jsonify({
                'message': 'Avatar setup completed successfully',
                'avatar': avatar_response
            }), 201
            
        except Exception as e:
            return jsonify({'error': f'Avatar setup failed: {str(e)}'}), 500
    
    @avatar_bp.route('/profile', methods=['GET'])
    @jwt_required()
    def get_avatar_profile():
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            
            # Get avatar
            avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            # Get body measurements
            measurements = measurements_repo.get_measurements_by_avatar_id(avatar.id)
            
            # Get garments
            garments = garments_repo.get_avatar_garments(avatar.id)
            
            # Build response
            avatar_response = avatar.to_dict()
            
            if measurements:
                avatar_response['bodyMeasurements'] = measurements.to_dict()
            
            avatar_response['garments'] = garments
            
            return jsonify({
                'avatar': avatar_response
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get avatar: {str(e)}'}), 500
    
    @avatar_bp.route('/profile', methods=['PUT'])
    @jwt_required()
    def update_avatar_profile():
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Get avatar
            avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            # Prepare update data
            update_data = {}
            
            field_mapping = {
                'fullName': 'full_name',
                'bio': 'bio',
                'age': 'age',
                'height': 'height',
                'heightUnit': 'height_unit',
                'weight': 'weight',
                'weightUnit': 'weight_unit',
                'avatarType': 'avatar_type',
                'genericAvatarStyle': 'generic_avatar_style',
                'biometricVerified': 'biometric_verified',
                'measurementMode': 'measurement_mode',
                'autoEstimated': 'auto_estimated',
                'shareWithWorld': 'share_with_world',
                'createAssistant': 'create_assistant',
                'createGreetingCards': 'create_greeting_cards',
                'publicProfile': 'public_profile',
                'allowConnections': 'allow_connections',
                'selectedGreetingTemplate': 'selected_greeting_template'
            }
            
            for frontend_field, backend_field in field_mapping.items():
                if frontend_field in data:
                    update_data[backend_field] = data[frontend_field]
            
            # Update avatar
            updated_avatar = avatar_repo.update_avatar(avatar.id, update_data)
            
            return jsonify({
                'message': 'Avatar updated successfully',
                'avatar': updated_avatar.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Avatar update failed: {str(e)}'}), 500
    
    @avatar_bp.route('/measurements', methods=['PUT'])
    @jwt_required()
    def update_measurements():
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Get avatar
            avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            # Prepare measurements data
            measurements_data = {
                'chest': data.get('chest'),
                'waist': data.get('waist'),
                'hips': data.get('hips'),
                'shoulder_width': data.get('shoulderWidth'),
                'inseam': data.get('inseam'),
                'arm_length': data.get('armLength'),
                'neck_size': data.get('neckSize')
            }
            
            # Check if measurements exist
            existing_measurements = measurements_repo.get_measurements_by_avatar_id(avatar.id)
            
            if existing_measurements:
                # Update existing measurements
                updated_measurements = measurements_repo.update_measurements(
                    avatar.id, measurements_data
                )
            else:
                # Create new measurements
                updated_measurements = measurements_repo.create_measurements(
                    avatar.id, measurements_data
                )
            
            return jsonify({
                'message': 'Measurements updated successfully',
                'measurements': updated_measurements.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Measurements update failed: {str(e)}'}), 500
    
    @avatar_bp.route('/garments', methods=['POST'])
    @jwt_required()
    def add_garment_to_wardrobe():
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            data = request.get_json()
            
            if not data or 'garmentId' not in data:
                return jsonify({'error': 'garmentId is required'}), 400
            
            # Get avatar
            avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            garment_id = data['garmentId']
            
            # Add garment
            garments_repo.add_garment(avatar.id, garment_id)
            
            return jsonify({
                'message': 'Garment added to wardrobe successfully'
            }), 201
            
        except Exception as e:
            return jsonify({'error': f'Failed to add garment: {str(e)}'}), 500
    
    @avatar_bp.route('/garments/<garment_id>', methods=['DELETE'])
    @jwt_required()
    def remove_garment_from_wardrobe(garment_id):
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            
            # Get avatar
            avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            # Remove garment
            garments_repo.remove_garment(avatar.id, garment_id)
            
            return jsonify({
                'message': 'Garment removed from wardrobe successfully'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to remove garment: {str(e)}'}), 500
    
    @avatar_bp.route('/garments', methods=['GET'])
    @jwt_required()
    def get_wardrobe():
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            
            # Get avatar
            avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            # Get garments
            garments = garments_repo.get_avatar_garments(avatar.id)
            
            return jsonify({
                'garments': garments
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get garments: {str(e)}'}), 500
    
    @avatar_bp.route('/public', methods=['GET'])
    def get_public_avatars():
        """
        Get public avatars
        
        Query params:
        - limit: Number of avatars to return (default: 20, max: 100)
        - offset: Offset for pagination (default: 0)
        """
        try:
            limit = request.args.get('limit', 20, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Validate limit
            if limit > 100:
                limit = 100
            
            # Get public avatars
            avatars = avatar_repo.get_public_avatars(limit, offset)
            
            avatars_list = [avatar.to_dict() for avatar in avatars]
            
            return jsonify({
                'avatars': avatars_list,
                'count': len(avatars_list),
                'limit': limit,
                'offset': offset
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get public avatars: {str(e)}'}), 500
    
    @avatar_bp.route('/<int:avatar_id>', methods=['GET'])
    def get_avatar_by_id(avatar_id):
        """
        Get avatar by ID (public endpoint)
        
        Only returns avatar if it's public
        """
        try:
            avatar = avatar_repo.get_avatar_by_id(avatar_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            if not avatar.public_profile:
                return jsonify({'error': 'Avatar is not public'}), 403
            
            # Get measurements if public
            measurements = measurements_repo.get_measurements_by_avatar_id(avatar.id)
            
            avatar_response = avatar.to_dict()
            
            if measurements:
                avatar_response['bodyMeasurements'] = measurements.to_dict()
            
            return jsonify({
                'avatar': avatar_response
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get avatar: {str(e)}'}), 500
    
    @avatar_bp.route('/profile', methods=['DELETE'])
    @jwt_required()
    def delete_avatar():
        try:
            current_user_id = get_jwt_identity()
            current_user_id = int(current_user_id)
            
            # Get avatar
            avatar = avatar_repo.get_avatar_by_user_id(current_user_id)
            
            if not avatar:
                return jsonify({'error': 'Avatar not found'}), 404
            
            # Delete avatar (cascade will handle measurements and garments)
            avatar_repo.delete_avatar(avatar.id)
            
            return jsonify({
                'message': 'Avatar deleted successfully'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to delete avatar: {str(e)}'}), 500
    
    return avatar_bp