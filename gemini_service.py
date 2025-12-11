from dotenv import load_dotenv
import os
import time
import base64
from google import genai
from google.genai import types

load_dotenv()


class GeminiService:
    def __init__(self):
        """Initialize Gemini client"""
        # Set API key - the client will automatically use GOOGLE_API_KEY env var
        # or you can pass it explicitly
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            # Will use default credentials or GOOGLE_API_KEY env var
            self.client = genai.Client()
        
        # Model configuration
        self.video_model = os.getenv('VEO_MODEL', 'veo-3.1-generate-preview')
        
        # Polling configuration
        self.poll_interval = int(os.getenv('VEO_POLL_INTERVAL', 10))  # seconds
        self.max_poll_time = int(os.getenv('VEO_MAX_POLL_TIME', 600))  # 10 minutes max
    
    def _get_mime_type(self, image_data: bytes) -> str:
        """Detect image MIME type from bytes"""
        # Check magic bytes
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        elif image_data[:2] == b'\xff\xd8':
            return 'image/jpeg'
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            return 'image/gif'
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return 'image/webp'
        else:
            # Default to JPEG
            return 'image/jpeg'
    
    def _validate_duration(self, duration: int) -> str:
        """
        Validate and convert duration to Veo-compatible value.
        Veo supports: 4, 6, or 8 seconds
        """
        if duration <= 4:
            return "4"
        elif duration <= 6:
            return "6"
        else:
            return "8"
    
    def generate_video_from_image(
        self,
        image_data: bytes,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        negative_prompt: str = None
    ) -> dict:
        """
        Generate video from image using Veo API
        
        Args:
            image_data: Image bytes from S3
            prompt: Text prompt describing desired video
            duration: Video duration (will be mapped to 4, 6, or 8 seconds)
            aspect_ratio: "16:9" or "9:16"
            negative_prompt: What to avoid in the video
            
        Returns:
            dict: Contains video_data (bytes), model, and metadata
        """
        try:
            print(f"🎬 Starting video generation with {self.video_model}...")
            
            # Detect MIME type
            mime_type = self._get_mime_type(image_data)
            print(f"📸 Image MIME type: {mime_type}")
            
            # Create image object for Veo
            image = types.Image(
                image_bytes=image_data,
                mime_type=mime_type
            )
            
            # Validate duration
            veo_duration = self._validate_duration(duration)
            print(f"⏱️ Video duration: {veo_duration} seconds")
            
            # Build config
            config_params = {
                "aspect_ratio": aspect_ratio,
                "duration_seconds": veo_duration,
            }
            
            if negative_prompt:
                config_params["negative_prompt"] = negative_prompt
            
            config = types.GenerateVideosConfig(**config_params)
            
            # Start video generation (async operation)
            print("🚀 Submitting video generation request...")
            operation = self.client.models.generate_videos(
                model=self.video_model,
                prompt=prompt,
                image=image,
                config=config
            )
            
            # Poll for completion
            start_time = time.time()
            while not operation.done:
                elapsed = time.time() - start_time
                
                if elapsed > self.max_poll_time:
                    raise TimeoutError(f"Video generation timed out after {self.max_poll_time} seconds")
                
                print(f"⏳ Waiting for video generation... ({int(elapsed)}s elapsed)")
                time.sleep(self.poll_interval)
                operation = self.client.operations.get(operation)
            
            print("✅ Video generation complete!")
            
            # Get the generated video
            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated")
            
            generated_video = operation.response.generated_videos[0]
            
            # Download video bytes
            print("📥 Downloading video...")
            self.client.files.download(file=generated_video.video)
            video_bytes = generated_video.video.video_bytes
            
            if not video_bytes:
                raise ValueError("Video download returned empty data")
            
            print(f"✅ Video downloaded: {len(video_bytes)} bytes")
            
            return {
                'video_data': video_bytes,
                'model': self.video_model,
                'duration': veo_duration,
                'aspect_ratio': aspect_ratio
            }
            
        except Exception as e:
            print(f"❌ Video generation error: {str(e)}")
            raise
    
    def generate_video_from_url(
        self,
        image_url: str,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        negative_prompt: str = None
    ) -> dict:
        """
        Generate video from image URL using Veo API
        
        Args:
            image_url: URL of the source image
            prompt: Text prompt describing desired video
            duration: Video duration (will be mapped to 4, 6, or 8 seconds)
            aspect_ratio: "16:9" or "9:16"
            negative_prompt: What to avoid in the video
            
        Returns:
            dict: Contains video_data (bytes), model, and metadata
        """
        import requests
        
        try:
            print(f"📥 Fetching image from URL: {image_url}")
            
            # Download image from URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            print(f"✅ Image downloaded: {len(image_data)} bytes")
            
            # Use the image-based generation
            return self.generate_video_from_image(
                image_data=image_data,
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt
            )
            
        except requests.RequestException as e:
            print(f"❌ Failed to download image: {str(e)}")
            raise ValueError(f"Failed to download image from URL: {str(e)}")
    
    def generate_video_text_only(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        negative_prompt: str = None
    ) -> dict:
        """
        Generate video from text prompt only (no image input)
        
        Args:
            prompt: Text prompt describing desired video
            duration: Video duration (will be mapped to 4, 6, or 8 seconds)
            aspect_ratio: "16:9" or "9:16"
            negative_prompt: What to avoid in the video
            
        Returns:
            dict: Contains video_data (bytes), model, and metadata
        """
        try:
            print(f"🎬 Starting text-to-video generation with {self.video_model}...")
            
            # Validate duration
            veo_duration = self._validate_duration(duration)
            print(f"⏱️ Video duration: {veo_duration} seconds")
            
            # Build config
            config_params = {
                "aspect_ratio": aspect_ratio,
                "duration_seconds": veo_duration,
            }
            
            if negative_prompt:
                config_params["negative_prompt"] = negative_prompt
            
            config = types.GenerateVideosConfig(**config_params)
            
            # Start video generation
            print("🚀 Submitting video generation request...")
            operation = self.client.models.generate_videos(
                model=self.video_model,
                prompt=prompt,
                config=config
            )
            
            # Poll for completion
            start_time = time.time()
            while not operation.done:
                elapsed = time.time() - start_time
                
                if elapsed > self.max_poll_time:
                    raise TimeoutError(f"Video generation timed out after {self.max_poll_time} seconds")
                
                print(f"⏳ Waiting for video generation... ({int(elapsed)}s elapsed)")
                time.sleep(self.poll_interval)
                operation = self.client.operations.get(operation)
            
            print("✅ Video generation complete!")
            
            # Get the generated video
            if not operation.response or not operation.response.generated_videos:
                raise ValueError("No video was generated")
            
            generated_video = operation.response.generated_videos[0]
            
            # Download video bytes
            print("📥 Downloading video...")
            self.client.files.download(file=generated_video.video)
            video_bytes = generated_video.video.video_bytes
            
            if not video_bytes:
                raise ValueError("Video download returned empty data")
            
            print(f"✅ Video downloaded: {len(video_bytes)} bytes")
            
            return {
                'video_data': video_bytes,
                'model': self.video_model,
                'duration': veo_duration,
                'aspect_ratio': aspect_ratio
            }
            
        except Exception as e:
            print(f"❌ Video generation error: {str(e)}")
            raise


gemini_service = GeminiService()