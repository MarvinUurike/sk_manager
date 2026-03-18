import os
from typing import Dict, Any
from aws_utils import get_client
from equipment import update_equipment

REGION = os.environ.get('REGION', 'eu-north-1')
PHOTOS_BUCKET = os.environ.get('PHOTOS_BUCKET')

def get_upload_url(equipment_id: str, content_type: str = 'image/jpeg') -> Dict[str, Any]:
    if not PHOTOS_BUCKET:
        raise ValueError("PHOTOS_BUCKET environment variable not set")
        
    object_name = f"equipment/{equipment_id}.jpg"
    s3_client = get_client('s3')
    
    # Generate presigned URL for PUT
    try:
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': PHOTOS_BUCKET,
                'Key': object_name,
                'ContentType': content_type
            },
            ExpiresIn=300 # 5 minutes
        )
        
        # The public URL where the photo will be available after upload
        public_url = f"https://{PHOTOS_BUCKET}.s3.{REGION}.amazonaws.com/{object_name}"
        
        # We proactively update the equipment record with this URL
        # If the upload fails, it will point to a broken image, but they can just upload again
        update_equipment(equipment_id, {'photo_url': public_url})
        
        return {
            'upload_url': url,
            'photo_url': public_url,
            'expires_in': 300
        }
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        raise ValueError(f"Could not generate upload URL: {str(e)}")

def delete_photo(equipment_id: str) -> Dict[str, str]:
    if not PHOTOS_BUCKET:
        raise ValueError("PHOTOS_BUCKET environment variable not set")
        
    object_name = f"equipment/{equipment_id}.jpg"
    
    try:
        get_client('s3').delete_object(
            Bucket=PHOTOS_BUCKET,
            Key=object_name
        )
        
        # Clear the photo_url from the equipment record
        update_equipment(equipment_id, {'photo_url': ''})
        
        return {"status": "photo deleted"}
    except Exception as e:
        print(f"Error deleting photo: {e}")
        raise ValueError(f"Could not delete photo: {str(e)}")
