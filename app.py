from flask import Flask, jsonify
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import timedelta
from auth_routes import init_auth_routes
from avatar_routes import init_avatar_routes
from garment_routes import init_garment_routes

# Load environment variables
load_dotenv()

app = Flask(__name__)

# CORS Configuration
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'mydb')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=4)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_ALGORITHM'] = 'HS256'

# Initialize extensions
mysql = MySQL(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)


# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token has expired',
        'message': 'The token has expired. Please login again.'
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'Invalid token',
        'message': 'Signature verification failed or token is malformed.'
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'error': 'Authorization required',
        'message': 'Request does not contain a valid access token.'
    }), 401


# Register blueprints
auth_bp = init_auth_routes(mysql)
app.register_blueprint(auth_bp)

avatar_bp = init_avatar_routes(mysql)
app.register_blueprint(avatar_bp)

garment_bp = init_garment_routes(mysql)
app.register_blueprint(garment_bp)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint that verifies both application and database connectivity
    """
    try:
        # Test database connection
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        
        return jsonify({
            'status': 'healthy',
            'message': 'Application is running and database is connected',
            'database': 'connected'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Database connection failed',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint - API documentation
    """
    return jsonify({
        'message': 'Avatar Setup Backend API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'root': '/',
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login',
                'logout': 'POST /api/auth/logout',
                'refresh': 'POST /api/auth/refresh',
                'me': 'GET /api/auth/me',
                'change_password': 'POST /api/auth/change-password'
            },
            'avatar': {
                'setup': 'POST /api/avatar/setup',
                'get_profile': 'GET /api/avatar/profile',
                'update_profile': 'PUT /api/avatar/profile',
                'delete_profile': 'DELETE /api/avatar/profile',
                'update_measurements': 'PUT /api/avatar/measurements',
                'add_garment': 'POST /api/avatar/garments',
                'remove_garment': 'DELETE /api/avatar/garments/<garment_id>',
                'get_wardrobe': 'GET /api/avatar/garments',
                'get_public_avatars': 'GET /api/avatar/public',
                'get_avatar_by_id': 'GET /api/avatar/<avatar_id>'
            },
            'garments': {
                'list': 'GET /api/garments/',
                'get': 'GET /api/garments/<garment_id>',
                'search': 'GET /api/garments/search?q=<query>',
                'by_brand': 'GET /api/garments/brands/<brand>',
                'by_category': 'GET /api/garments/categories/<category>',
                'top_rated': 'GET /api/garments/top-rated',
                'create': 'POST /api/garments/',
                'update': 'PUT /api/garments/<garment_id>',
                'delete': 'DELETE /api/garments/<garment_id>'
            }
        }
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'True') == 'True',
        use_reloader=False  # Disable reloader to avoid Windows socket issues
    )