"""
Helper utilities for image processing and base64 encoding
"""

import requests
from PIL import Image
import numpy as np
from io import BytesIO
import base64

def download_image(url):
    """
    Download image from URL or decode base64
    
    Args:
        url: Image URL (HTTP) or base64 string
        
    Returns:
        PIL Image object
    """
    try:
        # Check if it's a base64 string
        if url.startswith('data:image'):
            # Extract base64 data
            base64_data = url.split(',')[1]
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            return image
        else:
            # Regular URL download
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            return image
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        raise


def upload_to_storage(image_data, destination_path=None, thumbnail_size=(400, 400), quality=70):
    """
    Convert image to base64 string for Firestore storage
    
    Args:
        image_data: numpy array or PIL Image
        destination_path: Not used (kept for compatibility)
        thumbnail_size: Max dimensions for thumbnail (default 400x400)
        quality: JPEG quality 1-100 (default 70)
        
    Returns:
        Base64 encoded string (data URL format)
    """
    try:
        # Convert numpy array to PIL Image if needed
        if isinstance(image_data, np.ndarray):
            image = Image.fromarray(image_data.astype('uint8'))
        else:
            image = image_data
        
        # Resize image to reduce base64 size
        image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        
        # Convert to bytes with JPEG compression for smaller size
        img_byte_arr = BytesIO()
        # Convert RGBA to RGB if needed
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
        img_byte_arr.seek(0)
        
        # Convert to base64
        base64_data = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # Return as data URL
        return f"data:image/jpeg;base64,{base64_data}"
            
    except Exception as e:
        print(f"Error converting to base64: {str(e)}")
        return None


def create_thumbnail(image_data, size=(200, 200), quality=60):
    """
    Create a very small thumbnail for database storage
    
    Args:
        image_data: numpy array or PIL Image
        size: Thumbnail dimensions (default 200x200)
        quality: JPEG quality 1-100 (default 60)
        
    Returns:
        Base64 encoded thumbnail string (data URL format)
    """
    return upload_to_storage(image_data, thumbnail_size=size, quality=quality)


def resize_image(image, max_size=(800, 800)):
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: PIL Image
        max_size: Maximum dimensions (width, height)
        
    Returns:
        Resized PIL Image
    """
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def convert_to_grayscale(image):
    """Convert image to grayscale"""
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    return image.convert('L')


def normalize_image(image_array):
    """
    Normalize image array to [0, 1] range
    """
    return (image_array - image_array.min()) / (image_array.max() - image_array.min() + 1e-8)

