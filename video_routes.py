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
    
    # Default fashion video prompt
    DEFAULT_FASHION_PROMPT = """Create a cinematic fashion video showcasing this outfit with smooth, elegant camera movements. The video should highlight the clothing details and style with professional lighting and composition."""
    
    @video_bp.route('/generate', methods=['POST'])
    @jwt_required()
    def generate_video():
        """
        Generate video from image using Gemini Veo API
        
        Request body:
        {
            "image_key": "uuid.jpg",           // S3 image key (required)
            "prompt": "Custom prompt",          // Optional - uses fashion prompt by default
            "duration": 8,                      // Optional: 4, 6, or 8 seconds (default: 8)
            "aspect_ratio": "16:9",             // Optional: "16:9" or "9:16" (default: "16:9")
            "negative_prompt": "blur, shaky"    // Optional: what to avoid
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
            duration = data.get('duration', 8)
            aspect_ratio = data.get('aspect_ratio', '16:9')
            negative_prompt = data.get('negative_prompt')
            
            # Validate duration (Veo supports 4, 6, or 8 seconds)
            if duration not in [4, 6, 8]:
                return jsonify({
                    'success': False,
                    'error': 'Duration must be 4, 6, or 8 seconds'
                }), 400
            
            # Validate aspect ratio
            if aspect_ratio not in ['16:9', '9:16']:
                return jsonify({
                    'success': False,
                    'error': 'Aspect ratio must be "16:9" or "9:16"'
                }), 400
            
            # Check if image exists in S3
            if not s3_service.check_file_exists(image_key):
                return jsonify({
                    'success': False,
                    'error': 'Image not found in storage'
                }), 404
            
            # Get image from S3
            print(f"📸 Fetching image {image_key} from S3...")
            image_data, content_type = s3_service.get_image(image_key)
            
            # Prepare prompt
            prompt = custom_prompt if custom_prompt else DEFAULT_FASHION_PROMPT
            
            # Generate video using Gemini Veo API
            print(f"🎬 Generating video with Veo API...")
            video_result = gemini_service.generate_video_from_image(
                image_data=image_data,
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt
            )
            
            # Upload video to S3
            video_key = None
            video_url = None
            
            if video_result.get('video_data'):
                # Generate unique key for video
                video_key = f"videos/{uuid.uuid4()}.mp4"
                
                # Upload to S3
                print(f"☁️ Uploading video to S3 as {video_key}...")
                s3_service.s3_client.put_object(
                    Bucket=s3_service.bucket_name,
                    Key=video_key,
                    Body=video_result['video_data'],
                    ContentType='video/mp4'
                )
                
                video_url = f"https://{s3_service.bucket_name}.s3.{os.getenv('AWS_BUCKET_REGION')}.amazonaws.com/{video_key}"
                print(f"✅ Video uploaded to S3: {video_url}")
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
                    'duration': video_result.get('duration'),
                    'aspect_ratio': video_result.get('aspect_ratio'),
                    'model': video_result.get('model'),
                    'credits_used': VIDEO_GENERATION_COST
                }
            }), 201
            
        except TimeoutError as e:
            return jsonify({
                'success': False,
                'error': f'Video generation timed out: {str(e)}'
            }), 504
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
            print(f"❌ Video generation error: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'success': False,
                'error': f'Failed to generate video: {str(e)}'
            }), 500
    
    @video_bp.route('/generate-from-url', methods=['POST'])
    @jwt_required()
    def generate_video_from_url():
        """
        Generate video from image URL using Gemini Veo API
        
        Request body:
        {
            "image_url": "https://...",         // Image URL (required)
            "prompt": "Custom prompt",           // Optional
            "duration": 8,                       // Optional: 4, 6, or 8 seconds
            "aspect_ratio": "16:9",              // Optional: "16:9" or "9:16"
            "negative_prompt": "blur, shaky"     // Optional
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
            duration = data.get('duration', 8)
            aspect_ratio = data.get('aspect_ratio', '16:9')
            negative_prompt = data.get('negative_prompt')
            
            # Validate duration
            if duration not in [4, 6, 8]:
                return jsonify({
                    'success': False,
                    'error': 'Duration must be 4, 6, or 8 seconds'
                }), 400
            
            # Validate aspect ratio
            if aspect_ratio not in ['16:9', '9:16']:
                return jsonify({
                    'success': False,
                    'error': 'Aspect ratio must be "16:9" or "9:16"'
                }), 400
            
            # Prepare prompt
            prompt = custom_prompt if custom_prompt else DEFAULT_FASHION_PROMPT
            
            # Generate video
            video_result = gemini_service.generate_video_from_url(
                image_url=image_url,
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt
            )
            
            # Upload video to S3
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
            
            return jsonify({
                'success': True,
                'message': 'Video generated successfully',
                'data': {
                    'video_key': video_key,
                    'video_url': video_url,
                    'image_url': image_url,
                    'prompt': prompt,
                    'duration': video_result.get('duration'),
                    'aspect_ratio': video_result.get('aspect_ratio'),
                    'model': video_result.get('model'),
                    'credits_used': VIDEO_GENERATION_COST
                }
            }), 201
            
        except TimeoutError as e:
            return jsonify({
                'success': False,
                'error': f'Video generation timed out: {str(e)}'
            }), 504
        except Exception as e:
            import traceback
            print(f"❌ Video generation error: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'success': False,
                'error': f'Failed to generate video: {str(e)}'
            }), 500
    
    @video_bp.route('/generate-text', methods=['POST'])
    @jwt_required()
    def generate_video_text_only():
        """
        Generate video from text prompt only (no image)
        
        Request body:
        {
            "prompt": "Description of video",    // Required
            "duration": 8,                       // Optional: 4, 6, or 8 seconds
            "aspect_ratio": "16:9",              // Optional: "16:9" or "9:16"
            "negative_prompt": "blur, shaky"     // Optional
        }
        """
        try:
            data = request.get_json()
            
            # Validate request
            if not data or 'prompt' not in data:
                return jsonify({
                    'success': False,
                    'error': 'prompt is required'
                }), 400
            
            prompt = data.get('prompt')
            duration = data.get('duration', 8)
            aspect_ratio = data.get('aspect_ratio', '16:9')
            negative_prompt = data.get('negative_prompt')
            
            # Validate duration
            if duration not in [4, 6, 8]:
                return jsonify({
                    'success': False,
                    'error': 'Duration must be 4, 6, or 8 seconds'
                }), 400
            
            # Validate aspect ratio
            if aspect_ratio not in ['16:9', '9:16']:
                return jsonify({
                    'success': False,
                    'error': 'Aspect ratio must be "16:9" or "9:16"'
                }), 400
            
            # Generate video
            video_result = gemini_service.generate_video_text_only(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt
            )
            
            # Upload video to S3
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
            
            return jsonify({
                'success': True,
                'message': 'Video generated successfully',
                'data': {
                    'video_key': video_key,
                    'video_url': video_url,
                    'prompt': prompt,
                    'duration': video_result.get('duration'),
                    'aspect_ratio': video_result.get('aspect_ratio'),
                    'model': video_result.get('model'),
                    'credits_used': VIDEO_GENERATION_COST
                }
            }), 201
            
        except TimeoutError as e:
            return jsonify({
                'success': False,
                'error': f'Video generation timed out: {str(e)}'
            }), 504
        except Exception as e:
            import traceback
            print(f"❌ Video generation error: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'success': False,
                'error': f'Failed to generate video: {str(e)}'
            }), 500
    
    return video_bp