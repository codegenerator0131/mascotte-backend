"""
Credit routes for managing credit plans, transactions, and balances
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from credit_models import CreditTransactionRepository, CreditPlanRepository
from models import UserRepository

credit_bp = Blueprint('credit', __name__, url_prefix='/api/credits')


def init_credit_routes(mysql):
    """Initialize credit routes with database connection"""
    transaction_repo = CreditTransactionRepository(mysql)
    plan_repo = CreditPlanRepository(mysql)
    user_repo = UserRepository(mysql)
    
    @credit_bp.route('/balance', methods=['GET'])
    @jwt_required()
    def get_balance():
        """Get current user's credit balance"""
        try:
            user_id = get_jwt_identity()
            credits = user_repo.get_user_credits(int(user_id))
            
            if credits is None:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'credits': credits
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get balance: {str(e)}'}), 500
    
    @credit_bp.route('/plans', methods=['GET'])
    @jwt_required()
    def get_plans():
        """Get all available credit plans"""
        try:
            plans = plan_repo.get_all_plans()
            
            return jsonify({
                'plans': [plan.to_dict() for plan in plans]
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get plans: {str(e)}'}), 500
    
    @credit_bp.route('/transactions', methods=['GET'])
    @jwt_required()
    def get_transactions():
        """Get user's credit transaction history"""
        try:
            user_id = get_jwt_identity()
            
            # Get pagination parameters
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Limit the maximum records per request
            limit = min(limit, 100)
            
            transactions = transaction_repo.get_user_transactions(
                int(user_id), limit, offset
            )
            
            return jsonify({
                'transactions': [t.to_dict() for t in transactions],
                'limit': limit,
                'offset': offset
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get transactions: {str(e)}'}), 500
    
    @credit_bp.route('/transactions/stats', methods=['GET'])
    @jwt_required()
    def get_transaction_stats():
        """Get user's transaction statistics"""
        try:
            user_id = get_jwt_identity()
            stats = transaction_repo.get_transaction_stats(int(user_id))
            
            return jsonify({
                'stats': stats
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500
    
    @credit_bp.route('/deduct', methods=['POST'])
    @jwt_required()
    def deduct_credits():
        """Deduct credits from user account (for internal use)"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            credits = data.get('credits')
            description = data.get('description', 'Credit usage')
            reference_id = data.get('reference_id')
            metadata = data.get('metadata')
            
            if not credits or credits <= 0:
                return jsonify({'error': 'Invalid credits amount'}), 400
            
            # Deduct credits
            updated_user = user_repo.deduct_credits(int(user_id), credits)
            
            # Create transaction record
            transaction = transaction_repo.create_transaction(
                user_id=int(user_id),
                transaction_type='usage',
                credits=-credits,
                description=description,
                amount=0.0,
                status='completed',
                reference_id=reference_id,
                metadata=metadata
            )
            
            return jsonify({
                'message': 'Credits deducted successfully',
                'transaction': transaction.to_dict(),
                'remaining_credits': updated_user.credits
            }), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to deduct credits: {str(e)}'}), 500
    
    @credit_bp.route('/add', methods=['POST'])
    @jwt_required()
    def add_credits():
        """Add credits to user account (for admin/purchase use)"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            credits = data.get('credits')
            description = data.get('description', 'Credits added')
            transaction_type = data.get('transaction_type', 'purchase')
            amount = data.get('amount', 0.0)
            reference_id = data.get('reference_id')
            metadata = data.get('metadata')
            
            if not credits or credits <= 0:
                return jsonify({'error': 'Invalid credits amount'}), 400
            
            # Add credits
            updated_user = user_repo.add_credits(int(user_id), credits)
            
            # Create transaction record
            transaction = transaction_repo.create_transaction(
                user_id=int(user_id),
                transaction_type=transaction_type,
                credits=credits,
                description=description,
                amount=amount,
                status='completed',
                reference_id=reference_id,
                metadata=metadata
            )
            
            return jsonify({
                'message': 'Credits added successfully',
                'transaction': transaction.to_dict(),
                'total_credits': updated_user.credits
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to add credits: {str(e)}'}), 500
    
    return credit_bp