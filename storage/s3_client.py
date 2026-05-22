"""S3 client for handling file uploads and downloads."""
import logging
from typing import Optional, List, Dict, Any

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class S3Client(BaseModel):  # type: ignore[operator]
    """S3 client for handling file uploads and downloads."""
    
    bucket_name: str
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        
    def __init__(self, **data):
        """Initialize S3 client with provided credentials."""
        super().__init__(**data)
        
        # Initialize the boto3 S3 resource
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.s3_resource = boto3.resource(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
        else:
            # Use default credentials from environment or IAM roles
            self.s3_resource = boto3.resource('s3', region_name=self.region_name)
            
            
            
            
    def list_files(self, prefix: str = "") -> List[str]:
        """List files in an S3 bucket.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file names
        """
        try:
            files = []
            bucket = self.s3_resource.Bucket(self.bucket_name)
            
            for obj in bucket.objects.filter(Prefix=prefix):
                files.append(obj.key)
                
            logger.info(f"Found {len(files)} files with prefix '{prefix}'")
            return files
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
            
    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in an S3 bucket.
        
        Args:
            object_name: Name of the object in S3
            
        Returns:
            True if file exists, else False
        """
        try:
            self.s3_resource.Object(self.bucket_name, object_name).load()
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Failed to check existence of {object_name}: {e}")
            raise

# Module-level wrappers — routes import these directly
_s3_client_instance = S3Client()  # type: ignore[operator]

def upload_file(file_path: str, object_name: str) -> str:
    """Upload a file to S3 and return the object URL."""
    return _s3_client_instance.upload_file(file_path, object_name)

def download_file(object_name: str, dest_path: str) -> bool:
    """Download a file from S3 to dest_path."""
    return _s3_client_instance.download_file(object_name, dest_path)

def delete_file(object_name: str) -> bool:
    """Delete a file from S3."""
    return _s3_client_instance.delete_file(object_name)
