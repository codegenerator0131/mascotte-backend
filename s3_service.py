from dotenv import load_dotenv
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from werkzeug.datastructures import FileStorage
from PIL import Image
import io
import mimetypes

load_dotenv()

class S3Service:
    def __init__(self):
        """Initialize S3 client with configuration"""
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_BUCKET_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
        )
        self.bucket_name = os.getenv('AWS_IMAGE_BUCKET_NAME')
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    def _generate_unique_filename(self, original_filename):
        """Generate a unique filename using UUID"""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
        return f"{uuid.uuid4()}.{ext}"

    def _allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def _optimize_image(self, file_data, mimetype):
        """Optimize image using Pillow (similar to Sharp in Node.js)"""
        try:
            image = Image.open(io.BytesIO(file_data))
            
            # Convert RGBA to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # Resize if image is too large (max 2000px on longest side)
            max_dimension = 2000
            if max(image.size) > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

            # Save optimized image to bytes
            output = io.BytesIO()
            
            # Determine format and optimize
            if mimetype == 'image/jpeg' or mimetype == 'image/jpg':
                image.save(output, format='JPEG', quality=85, optimize=True)
            elif mimetype == 'image/png':
                image.save(output, format='PNG', optimize=True)
            elif mimetype == 'image/webp':
                image.save(output, format='WEBP', quality=85)
            elif mimetype == 'image/gif':
                image.save(output, format='GIF', optimize=True)
            else:
                image.save(output, format='JPEG', quality=85, optimize=True)
            
            output.seek(0)
            return output.getvalue()
        except Exception as e:
            print(f"Error optimizing image: {str(e)}")
            return file_data

    def upload_image(self, file: FileStorage):
        """
        Upload a single image file to S3
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            dict: Contains key, bucket, url, and file metadata
        """
        if not file:
            raise ValueError("No file provided")

        if not self._allowed_file(file.filename):
            raise ValueError(f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}")

        # Read file data ONCE and store it
        file.seek(0)  # Make sure we're at the beginning of the file
        file_data = file.read()
        
        # Check if file_data is empty
        if not file_data:
            raise ValueError("File is empty or could not be read")
        
        # Check file size
        if len(file_data) > self.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size / (1024*1024)}MB")

        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename)
        
        # Optimize image
        mimetype = file.content_type or mimetypes.guess_type(file.filename)[0] or 'image/jpeg'
        
        # IMPORTANT: Pass file_data, not file
        optimized_data = self._optimize_image(file_data, mimetype)

        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=optimized_data,
                ContentType=mimetype
            )

            # Generate URL
            url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_BUCKET_REGION')}.amazonaws.com/{unique_filename}"

            return {
                'key': unique_filename,
                'bucket': self.bucket_name,
                'url': url,
                'originalname': file.filename,
                'size': len(optimized_data),
                'mimetype': mimetype
            }

        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    def upload_multiple_images(self, files):
        """
        Upload multiple images to S3
        
        Args:
            files: List of FileStorage objects
            
        Returns:
            list: List of upload results
        """
        results = []
        errors = []

        for file in files:
            try:
                result = self.upload_image(file)
                results.append(result)
            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })

        return {
            'successful': results,
            'failed': errors
        }

    def get_image(self, key):
        """
        Get image from S3
        
        Args:
            key: S3 object key
            
        Returns:
            tuple: (file_data, content_type)
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read(), response['ContentType']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"Image not found: {key}")
            raise Exception(f"Failed to retrieve image: {str(e)}")

    def get_signed_url(self, key, expiration=3600):
        """
        Generate a presigned URL for an image
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            str: Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate signed URL: {str(e)}")

    def delete_image(self, key):
        """
        Delete an image from S3
        
        Args:
            key: S3 object key
            
        Returns:
            bool: True if successful
        """
        # Prevent deletion of default images
        if key in ['default.png', 'default-cover.png', None]:
            return False

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete image: {str(e)}")

    def check_file_exists(self, key):
        """
        Check if a file exists in S3
        
        Args:
            key: S3 object key
            
        Returns:
            bool: True if file exists
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise Exception(f"Failed to check file existence: {str(e)}")

    def list_images(self, prefix='', max_keys=100):
        """
        List images in S3 bucket
        
        Args:
            prefix: Filter by key prefix
            max_keys: Maximum number of keys to return
            
        Returns:
            list: List of image objects
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            if 'Contents' not in response:
                return []

            return [
                {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': f"https://{self.bucket_name}.s3.{os.getenv('AWS_BUCKET_REGION')}.amazonaws.com/{obj['Key']}"
                }
                for obj in response['Contents']
            ]
        except ClientError as e:
            raise Exception(f"Failed to list images: {str(e)}")

s3_service = S3Service()