from dotenv import load_dotenv
import os
from google import genai
import requests
import base64

load_dotenv()


class GeminiService:
    def __init__(self):
        """Initialize Gemini client with API key"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=self.api_key)
        self.use_mock = os.getenv('USE_MOCK_VIDEO', 'true').lower() == 'true'
        
    def generate_video_from_image(self, image_data, prompt=None, duration=None):
        """
        Generate video from image
        Uses mock video for testing since Veo is not available in all regions
        """
        try:
            if not prompt:
                prompt = "Create a cinematic fashion video showcasing this outfit with smooth, elegant camera movements."
            
            if not duration:
                duration = 7
            
            print(f"Generating video...")
            print(f"Prompt: {prompt}")
            print(f"Use Mock: {self.use_mock}")
            
            # Use mock video for testing
            if self.use_mock:
                return self._generate_mock_video(image_data, prompt, duration)
            else:
                # Try real video generation (requires API access)
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
        # You can replace this with your own sample video
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
        Attempt real video generation
        This will fail if Veo is not available in your region
        """
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Try REST API
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1:generateVideo"
        
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': self.api_key
        }
        
        payload = {
            'prompt': {
                'text': prompt,
                'image': {
                    'bytes': image_base64,
                    'mimeType': 'image/jpeg'
                }
            },
            'videoConfig': {
                'duration': f"{duration}s",
                'aspectRatio': '9:16',
                'fps': 24
            }
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'video' in result:
                video_info = result['video']
                
                if 'uri' in video_info:
                    return {
                        'video_data': None,
                        'video_url': video_info['uri'],
                        'prompt': prompt,
                        'duration': duration,
                        'model': 'veo-3.1'
                    }
                elif 'bytes' in video_info:
                    video_data = base64.b64decode(video_info['bytes'])
                    return {
                        'video_data': video_data,
                        'video_url': None,
                        'prompt': prompt,
                        'duration': duration,
                        'model': 'veo-3.1'
                    }
        
        raise Exception(f"API returned status {response.status_code}: {response.text}")
    
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