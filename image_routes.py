from flask import Blueprint, request, jsonify, send_file
from s3_service import s3_service
from io import BytesIO

# Create Blueprint
image_bp = Blueprint('images', __name__, url_prefix='/api/images')


@image_bp.route('/upload', methods=['POST'])
def upload_image():
    """
    Upload a single image
    
    Expected: multipart/form-data with 'image' field
    """
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Additional check: verify file has content
        if not file:
            return jsonify({
                'success': False,
                'error': 'File object is invalid'
            }), 400

        # Upload to S3
        result = s3_service.upload_image(file)

        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'data': result
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        # Better error logging
        import traceback
        print(f"Upload error: {str(e)}")
        print(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Failed to upload image: {str(e)}'
        }), 500


@image_bp.route('/upload/multiple', methods=['POST'])
def upload_multiple_images():
    """
    Upload multiple images
    
    Expected: multipart/form-data with 'images' field (multiple files)
    """
    try:
        # Check if files are present
        if 'images' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image files provided'
            }), 400

        files = request.files.getlist('images')

        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400

        # Upload to S3
        result = s3_service.upload_multiple_images(files)

        return jsonify({
            'success': True,
            'message': f'Uploaded {len(result["successful"])} images successfully',
            'data': result
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to upload images: {str(e)}'
        }), 500

@image_bp.route('/<key>', methods=['GET'])
def get_image(key):
    """
    Get and display an image by key
    
    Args:
        key: S3 object key (filename)
    """
    try:
        # Get image from S3
        image_data, content_type = s3_service.get_image(key)

        # Return image as response
        return send_file(
            BytesIO(image_data),
            mimetype=content_type,
            as_attachment=False,
            download_name=key
        )

    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Image not found'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve image: {str(e)}'
        }), 500


@image_bp.route('/<key>/url', methods=['GET'])
def get_image_url(key):
    """
    Get a presigned URL for an image
    
    Args:
        key: S3 object key (filename)
    
    Query params:
        expiration: URL expiration time in seconds (default 3600)
    """
    try:
        expiration = request.args.get('expiration', 3600, type=int)
        
        # Check if file exists
        if not s3_service.check_file_exists(key):
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404

        # Generate signed URL
        url = s3_service.get_signed_url(key, expiration)

        return jsonify({
            'success': True,
            'data': {
                'key': key,
                'url': url,
                'expires_in': expiration
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate URL: {str(e)}'
        }), 500


@image_bp.route('/<key>', methods=['DELETE'])
def delete_image(key):
    """
    Delete an image by key
    
    Args:
        key: S3 object key (filename)
    """
    try:
        # Delete from S3
        success = s3_service.delete_image(key)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Cannot delete default or system images'
            }), 403

        return jsonify({
            'success': True,
            'message': 'Image deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to delete image: {str(e)}'
        }), 500


@image_bp.route('/list', methods=['GET'])
def list_images():
    """
    List all images in the bucket
    
    Query params:
        prefix: Filter by key prefix
        max_keys: Maximum number of images to return (default 100)
    """
    try:
        prefix = request.args.get('prefix', '')
        max_keys = request.args.get('max_keys', 100, type=int)

        images = s3_service.list_images(prefix, max_keys)

        return jsonify({
            'success': True,
            'data': {
                'images': images,
                'count': len(images)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to list images: {str(e)}'
        }), 500


@image_bp.route('/exists/<key>', methods=['GET'])
def check_image_exists(key):
    """
    Check if an image exists
    
    Args:
        key: S3 object key (filename)
    """
    try:
        exists = s3_service.check_file_exists(key)

        return jsonify({
            'success': True,
            'data': {
                'key': key,
                'exists': exists
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to check image: {str(e)}'
        }), 500