from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from s3_service import s3_service
from gemini_service import gemini_service
from io import BytesIO
import uuid
import os

video_bp = Blueprint('video', __name__, url_prefix='/api/video')


def init_video_routes(mysql):
    """Initialize video routes with database connection"""
    
    # Cost configuration
    VIDEO_GENERATION_COST = 50  # 50 credits per video generation
    
    @video_bp.route('/generate', methods=['POST'])
    @jwt_required()
    def generate_video():
        """
        Generate video from image using Gemini AI
        
        Request body:
        {
            "image_key": "uuid.jpg",  // S3 image key
            "prompt": "Optional custom prompt",  // Optional
            "duration": 7  // Optional, 5-10 seconds
        }
        """
        try:
            data = request.get_json()
            
            # Validate request
            if not data or 'image_key' not in data:
                return jsonify({
                    'success': False,
                    'error': 'image_key is required'
                }), 400
            
            image_key = data.get('image_key')
            custom_prompt = data.get('prompt')
            duration = data.get('duration', 7)
            
            # Validate duration
            if duration < 5 or duration > 10:
                return jsonify({
                    'success': False,
                    'error': 'Duration must be between 5 and 10 seconds'
                }), 400
            
            # Check if image exists in S3
            if not s3_service.check_file_exists(image_key):
                return jsonify({
                    'success': False,
                    'error': 'Image not found in storage'
                }), 404
            
            # Get image from S3
            print(f"Fetching image {image_key} from S3...")
            image_data, content_type = s3_service.get_image(image_key)
            
            # Prepare prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = f"Please generate a fashion video using this image. The duration should be {duration} seconds. Create smooth, cinematic movements that showcase the fashion item elegantly."
            
            # Generate video using Gemini AI
            print(f"Generating video with Gemini AI...")
            video_result = gemini_service.generate_video_from_image(
                image_data=image_data,
                prompt=prompt,
                duration=duration
            )
            
            # Upload video to S3
            video_key = None
            video_url = None
            
            if video_result.get('video_data'):
                # Generate unique key for video
                video_key = f"videos/{uuid.uuid4()}.mp4"
                
                # Upload to S3
                print(f"Uploading video to S3 as {video_key}...")
                s3_service.s3_client.put_object(
                    Bucket=s3_service.bucket_name,
                    Key=video_key,
                    Body=video_result['video_data'],
                    ContentType='video/mp4'
                )
                
                video_url = f"https://{s3_service.bucket_name}.s3.{os.getenv('AWS_BUCKET_REGION')}.amazonaws.com/{video_key}"
                print(f"✅ Video uploaded to S3: {video_url}")
                
            elif video_result.get('video_url'):
                video_url = video_result['video_url']
                print(f"✅ Using video URL: {video_url}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'Video generation returned no data'
                }), 500
            
            
            return jsonify({
                'success': True,
                'message': 'Video generated successfully',
                'data': {
                    'video_key': video_key,
                    'video_url': video_url,
                    'image_key': image_key,
                    'prompt': prompt,
                    'duration': duration,
                    'model': video_result.get('model'),
                    'credits_used': VIDEO_GENERATION_COST,
                    'note': video_result.get('note')  # For mock video indicator
                }
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except FileNotFoundError as e:
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        except Exception as e:
            import traceback
            print(f"Video generation error: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'success': False,
                'error': f'Failed to generate video: {str(e)}'
            }), 500
    
    @video_bp.route('/generate-from-url', methods=['POST'])
    @jwt_required()
    def generate_video_from_url():
        """
        Generate video from image URL using Gemini AI
        
        Request body:
        {
            "image_url": "https://...",
            "prompt": "Optional custom prompt",
            "duration": 7
        }
        """
        try:
            current_user_id = int(get_jwt_identity())
            data = request.get_json()
            
            # Validate request
            if not data or 'image_url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'image_url is required'
                }), 400
            
            image_url = data.get('image_url')
            custom_prompt = data.get('prompt')
            duration = data.get('duration', 7)
            
            # Prepare prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = f"Please generate a fashion video using this image. The duration should be {duration} seconds."
            
            # Generate video
            video_result = gemini_service.generate_video_from_url(
                image_url=image_url,
                prompt=prompt,
                duration=duration
            )
            
            # Upload video to S3 if needed
            video_key = None
            video_url = None
            
            if video_result.get('video_data'):
                video_key = f"videos/{uuid.uuid4()}.mp4"
                
                s3_service.s3_client.put_object(
                    Bucket=s3_service.bucket_name,
                    Key=video_key,
                    Body=video_result['video_data'],
                    ContentType='video/mp4'
                )
                
                video_url = f"https://{s3_service.bucket_name}.s3.{os.getenv('AWS_BUCKET_REGION')}.amazonaws.com/{video_key}"
            elif video_result.get('video_url'):
                video_url = video_result['video_url']
            
            return jsonify({
                'success': True,
                'message': 'Video generated successfully',
                'data': {
                    'video_key': video_key,
                    'video_url': video_url,
                    'prompt': prompt,
                    'duration': duration,
                    'credits_used': VIDEO_GENERATION_COST,
                    'note': video_result.get('note')
                }
            }), 201
            
        except Exception as e:
            import traceback
            print(f"Video generation error: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'success': False,
                'error': f'Failed to generate video: {str(e)}'
            }), 500
    
    return video_bp