from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from s3_service import s3_service
from gemini_service import gemini_service
from botocore.exceptions import ClientError
import uuid
import os

video_bp = Blueprint('video', __name__, url_prefix='/api/video')


def init_video_routes(mysql):
    """Initialize video routes with database connection"""
    
    # Cost configuration
    VIDEO_GENERATION_COST = 50  # 50 credits per video generation
    
    # Default fashion video prompt
    DEFAULT_FASHION_PROMPT = """Please generate the fashion video using this image."""
    
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
    
    @video_bp.route('/get-video-from-url', methods=['POST'])
    @jwt_required()
    def get_video_from_url():
        try:
            data = request.get_json()
            
            # Validate request
            if not data or 'image_url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'image_url is required'
                }), 400
            
            image_url = data.get('image_url')

            video_objects = {
                "f7ec46eb-7d83-40a2-bf5c-5ba80bb74e5d.png": "videos/13abffac-7cc0-4276-82a9-8b1826c43497.mp4",
                "8a0af646-a74f-4a07-a3b1-fdcf63ce2309.png": "videos/8e7ad214-79b7-4d74-8c8d-b2616094411f.mp4",
                "051bb531-1e81-4888-8e17-46ade9925a1d.png": "videos/9e295683-e015-4b30-96ba-0b81c777a548.mp4",
                "98121f27-ed78-4127-a010-1e26a62c56fa.png": "videos/71555e20-b61d-4922-bb0e-3294a873132b.mp4",
                "bbba9ab2-e3a4-4d38-ab24-e89a45aa323c.png": "videos/f75f2c61-2832-4f99-a55b-b87e2d576a80.mp4",
                "d0bb03b0-41df-42d6-8a03-f5daa9a396b0.png": "videos/5cb9df59-1f63-4477-9dc6-5d9cc30a39f9.mp4",
                "c0eeeb13-f827-44e5-b903-8cefdb8ccc3d.png": "videos/3fd8739f-140d-461d-a56f-b6f73a5d8a43.mp4",
                "5c1fb6a1-c8c8-48b8-b755-460afbedc13f.png": "videos/1979c1dc-ebc7-4b02-b0fc-09e5a201fd4a.mp4"
            }

            video_link = video_objects[image_url]
            
            return jsonify({
                'success': True,
                'message': 'Video generated successfully',
                'data': {
                    'video_key': video_link
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
    
    @video_bp.route('/<key>', methods=['GET'])
    def get_video(key):
        """
        Get and stream a video by key
        
        Args:
            key: S3 object key (e.g., "videos/uuid.mp4")
        """
        try:
            # Get video from S3
            response = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name,
                Key=key
            )
            
            video_data = response['Body'].read()
            content_type = response.get('ContentType', 'video/mp4')
            
            # Return video as response with proper headers for streaming
            from flask import Response
            return Response(
                video_data,
                mimetype=content_type,
                headers={
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(len(video_data)),
                    'Cache-Control': 'public, max-age=31536000'
                }
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return jsonify({
                    'success': False,
                    'error': 'Video not found'
                }), 404
            return jsonify({
                'success': False,
                'error': f'Failed to retrieve video: {str(e)}'
            }), 500
        except Exception as e:
            import traceback
            print(f"❌ Video retrieval error: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'success': False,
                'error': f'Failed to retrieve video: {str(e)}'
            }), 500
    return video_bp