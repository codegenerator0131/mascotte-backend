from flask import Flask, jsonify
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'mydb')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)


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
    Root endpoint
    """
    return jsonify({
        'message': 'Flask MySQL Backend',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'root': '/'
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