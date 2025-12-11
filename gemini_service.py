from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import requests
import base64
import time
import io
from PIL import Image

load_dotenv()


class GeminiService:
    def __init__(self):
        """Initialize Gemini client with API key"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=self.api_key)
        self.use_mock = os.getenv('USE_MOCK_VIDEO', 'false').lower() == 'true'
        
    def generate_video_from_image(self, image_data, prompt=None, duration=None):
        """
        Generate video from image using Veo 3.1
        
        Args:
            image_data: Binary image data
            prompt: Text prompt for video generation (optional)
            duration: Video duration in seconds (5-10s supported)
            
        Returns:
            dict: Contains video data and metadata
        """
        try:
            if not prompt:
                prompt = "Create a cinematic fashion video showcasing this outfit with smooth, elegant camera movements. The video should highlight the clothing details and style with professional lighting and composition."
            
            if not duration:
                duration = 7
            
            print(f"Generating video...")
            print(f"Prompt: {prompt}")
            print(f"Use Mock: {self.use_mock}")
            
            # Use mock video for testing
            if self.use_mock:
                return self._generate_mock_video(image_data, prompt, duration)
            else:
                # Try real video generation with Veo 3.1
                try:
                    return self._generate_real_video(image_data, prompt, duration)
                except Exception as e:
                    print(f"Real video generation failed: {str(e)}")
                    print("Falling back to mock video...")
                    return self._generate_mock_video(image_data, prompt, duration)
            
        except Exception as e:
            print(f"Video generation error: {str(e)}")
            raise Exception(f"Video generation failed: {str(e)}")
    
    def _generate_mock_video(self, image_data, prompt, duration):
        """Generate a mock video response for testing"""
        print("✅ Using mock video for testing")
        
        # Use a sample fashion/model video URL
        mock_video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        
        return {
            'video_data': None,
            'video_url': mock_video_url,
            'prompt': prompt,
            'duration': duration,
            'model': 'mock-video-v1',
            'note': 'Mock video for testing. Set USE_MOCK_VIDEO=false for real generation.'
        }
    
    def _generate_real_video(self, image_data, prompt, duration):
        """
        Generate real video using Veo 3.1
        Based on official Gemini API example
        """
        try:
            print("🎬 Starting real video generation with Veo 3.1...")
            
            # Step 1: Convert image_data to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            print(f"✅ Image loaded: {pil_image.size}")
            
            # Step 2: Generate video with Veo 3.1 using the image
            print("🎥 Generating video with Veo 3.1...")
            operation = self.client.models.generate_videos(
                model="veo-3.1-generate-preview",
                prompt=prompt,
                image=pil_image,
            )
            
            print(f"⏳ Operation started: {operation.name}")
            
            # Step 3: Poll the operation status until the video is ready
            max_wait_time = 300  # 5 minutes max
            elapsed_time = 0
            poll_interval = 10  # Check every 10 seconds
            
            while not operation.done and elapsed_time < max_wait_time:
                print(f"⏳ Waiting for video generation... ({elapsed_time}s elapsed)")
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                operation = self.client.operations.get(operation)
            
            if not operation.done:
                raise Exception(f"Video generation timed out after {max_wait_time} seconds")
            
            print("✅ Video generation completed!")
            
            # Step 4: Get the generated video
            video = operation.response.generated_videos[0]
            
            # Download the video data
            print("📥 Downloading video...")
            video_bytes = self.client.files.download(file=video.video)
            
            # Convert to bytes if needed
            if hasattr(video_bytes, 'read'):
                video_data = video_bytes.read()
            else:
                video_data = video_bytes
            
            print(f"✅ Video downloaded: {len(video_data)} bytes")
            
            return {
                'video_data': video_data,
                'video_url': None,
                'prompt': prompt,
                'duration': duration,
                'model': 'veo-3.1-generate-preview',
                'generation_time': elapsed_time
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Real video generation failed: {error_msg}")
            
            # Check for specific error types
            if "not supported" in error_msg.lower() or "not found" in error_msg.lower():
                raise Exception("Veo 3.1 is not available in your region or account. Please use USE_MOCK_VIDEO=true")
            elif "quota" in error_msg.lower():
                raise Exception("API quota exceeded. Please check your Gemini API usage limits.")
            else:
                raise Exception(f"Video generation failed: {error_msg}")
    
    def generate_video_from_url(self, image_url, prompt=None, duration=None):
        """Generate video from image URL"""
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = response.content
            
            return self.generate_video_from_image(image_data, prompt, duration)
            
        except Exception as e:
            raise Exception(f"Failed to generate video from URL: {str(e)}")


gemini_service = GeminiService()