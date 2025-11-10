"""
Garment routes for shopping and browsing garments
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from garment_models import GarmentRepository

garment_bp = Blueprint('garment', __name__, url_prefix='/api/garments')

def init_garment_routes(mysql):
    """Initialize garment routes with database connection"""
    garment_repo = GarmentRepository(mysql)
    
    @garment_bp.route('/', methods=['GET'])
    def get_garments():
        try:
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            if limit > 100:
                limit = 100
            
            filters = {}
            
            if request.args.get('brand'):
                filters['brand'] = request.args.get('brand')
            
            if request.args.get('category'):
                filters['category'] = request.args.get('category')
            
            if request.args.get('style'):
                filters['style'] = request.args.get('style')
            
            if request.args.get('minPrice'):
                filters['min_price'] = request.args.get('minPrice', type=float)
            
            if request.args.get('maxPrice'):
                filters['max_price'] = request.args.get('maxPrice', type=float)
            
            if request.args.get('search'):
                filters['search'] = request.args.get('search')
            
            garments = garment_repo.get_all_garments(limit, offset, filters)
            
            return jsonify({
                'garments': [g.to_dict() for g in garments],
                'count': len(garments),
                'limit': limit,
                'offset': offset
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get garments: {str(e)}'}), 500
    
    @garment_bp.route('/<int:garment_id>', methods=['GET'])
    def get_garment(garment_id):
        """Get garment by ID"""
        try:
            garment = garment_repo.get_garment_by_id(garment_id)
            
            if not garment:
                return jsonify({'error': 'Garment not found'}), 404
            
            if not garment.available:
                return jsonify({'error': 'Garment not available'}), 404
            
            return jsonify({
                'garment': garment.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get garment: {str(e)}'}), 500
    
    @garment_bp.route('/search', methods=['GET'])
    def search_garments():
        try:
            search_query = request.args.get('q')
            
            if not search_query:
                return jsonify({'error': 'Search query is required'}), 400
            
            limit = request.args.get('limit', 20, type=int)
            
            garments = garment_repo.search_garments(search_query, limit)
            
            return jsonify({
                'garments': [g.to_dict() for g in garments],
                'count': len(garments),
                'query': search_query
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Search failed: {str(e)}'}), 500
    
    @garment_bp.route('/brands/<brand>', methods=['GET'])
    def get_garments_by_brand(brand):
        try:
            limit = request.args.get('limit', 20, type=int)
            
            garments = garment_repo.get_garments_by_brand(brand, limit)
            
            return jsonify({
                'garments': [g.to_dict() for g in garments],
                'count': len(garments),
                'brand': brand
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get garments: {str(e)}'}), 500
    
    @garment_bp.route('/categories/<category>', methods=['GET'])
    def get_garments_by_category(category):
        try:
            limit = request.args.get('limit', 20, type=int)
            
            garments = garment_repo.get_garments_by_category(category, limit)
            
            return jsonify({
                'garments': [g.to_dict() for g in garments],
                'count': len(garments),
                'category': category
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get garments: {str(e)}'}), 500
    
    @garment_bp.route('/top-rated', methods=['GET'])
    def get_top_rated():
        try:
            limit = request.args.get('limit', 10, type=int)
            
            garments = garment_repo.get_top_rated_garments(limit)
            
            return jsonify({
                'garments': [g.to_dict() for g in garments],
                'count': len(garments)
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get top rated garments: {str(e)}'}), 500
    
    @garment_bp.route('/', methods=['POST'])
    @jwt_required()
    def create_garment():
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            required_fields = ['name', 'brand', 'price']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'{field} is required'}), 400
            
            garment_data = {
                'name': data['name'],
                'brand': data['brand'],
                'price': data['price'],
                'rating': data.get('rating', 0),
                'image_url': data.get('imageUrl'),
                'description': data.get('description'),
                'category': data.get('category'),
                'style': data.get('style'),
                'available': data.get('available', True)
            }
            
            garment = garment_repo.create_garment(garment_data)
            
            return jsonify({
                'message': 'Garment created successfully',
                'garment': garment.to_dict()
            }), 201
            
        except Exception as e:
            return jsonify({'error': f'Failed to create garment: {str(e)}'}), 500
    
    @garment_bp.route('/<int:garment_id>', methods=['PUT'])
    @jwt_required()
    def update_garment(garment_id):
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            garment_data = {}
            
            field_mapping = {
                'name': 'name',
                'brand': 'brand',
                'price': 'price',
                'rating': 'rating',
                'imageUrl': 'image_url',
                'description': 'description',
                'category': 'category',
                'style': 'style',
                'available': 'available'
            }
            
            for frontend_field, backend_field in field_mapping.items():
                if frontend_field in data:
                    garment_data[backend_field] = data[frontend_field]
            
            garment = garment_repo.update_garment(garment_id, garment_data)
            
            if not garment:
                return jsonify({'error': 'Garment not found'}), 404
            
            return jsonify({
                'message': 'Garment updated successfully',
                'garment': garment.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to update garment: {str(e)}'}), 500
    
    @garment_bp.route('/<int:garment_id>', methods=['DELETE'])
    @jwt_required()
    def delete_garment(garment_id):
        try:
            garment_repo.delete_garment(garment_id)
            
            return jsonify({
                'message': 'Garment deleted successfully'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to delete garment: {str(e)}'}), 500
    
    return garment_bp