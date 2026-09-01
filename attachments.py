import os
import struct
from typing import Union, Tuple, Dict, Any


def get_image_dimensions(filepath: str) -> Tuple[int, int]:
    """
    Extract image dimensions for PNG, JPEG, GIF, BMP files using header bytes.
    Returns (width, height) or raises ValueError if unsupported format.
    """
    with open(filepath, 'rb') as f:
        header = f.read(30)
        if len(header) < 24:
            raise ValueError("File too small to be a valid image")
        
        # PNG: 8-byte signature, then IHDR chunk
        if header[:8] == b'\x89PNG\r\n\x1a\n':
            if header[12:16] != b'IHDR':
                raise ValueError("Invalid PNG: missing IHDR")
            width = struct.unpack('>I', header[16:20])[0]
            height = struct.unpack('>I', header[20:24])[0]
            return (width, height)
        
        # JPEG: starts with FF D8, then SOF0 marker
        if header[:2] == b'\xff\xd8':
            # Search for SOF0 marker (0xFF 0xC0) or SOF2 (0xFF 0xC2)
            pos = 2
            while pos < len(header) - 1:
                if header[pos] == 0xFF and header[pos+1] in (0xC0, 0xC2):
                    # SOF marker found: length (2 bytes), precision (1), height (2), width (2)
                    height = struct.unpack('>H', header[pos+5:pos+7])[0]
                    width = struct.unpack('>H', header[pos+7:pos+9])[0]
                    return (width, height)
                pos += 1
            raise ValueError("Could not find SOF marker in JPEG")
        
        # GIF: 6-byte signature (GIF87a or GIF89a), then width/height (little-endian)
        if header[:6] in (b'GIF87a', b'GIF89a'):
            width = struct.unpack('<H', header[6:8])[0]
            height = struct.unpack('<H', header[8:10])[0]
            return (width, height)
        
        # BMP: starts with 'BM', offset to pixel data at bytes 10-14, width/height at bytes 18-22/22-26
        if header[:2] == b'BM':
            width = struct.unpack('<I', header[18:22])[0]
            height = struct.unpack('<I', header[22:26])[0]
            return (width, height)
        
        raise ValueError("Unsupported image format")


def process_attachment(filepath: str) -> Dict[str, Any]:
    """
    Process a file attachment. Returns a dictionary with:
    - 'type': 'image' or 'text'
    - 'size': file size in bytes
    - For images: 'dimensions' as (width, height) tuple
    - For text: 'content' as string
    Raises FileNotFoundError if file does not exist.
    Raises ValueError if file type is not supported.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    file_size = os.path.getsize(filepath)
    
    # Try to detect image by magic bytes (first bytes)
    with open(filepath, 'rb') as f:
        magic = f.read(8)
        f.seek(0)
    
    # Image magic bytes
    image_magic = {
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'\xff\xd8\xff': 'JPEG',  # first 3 bytes
        b'GIF87a': 'GIF',
        b'GIF89a': 'GIF',
        b'BM': 'BMP',
    }
    
    is_image = False
    for magic_bytes, fmt in image_magic.items():
        if magic[:len(magic_bytes)] == magic_bytes:
            is_image = True
            break
    
    if is_image:
        dimensions = get_image_dimensions(filepath)
        return {
            'type': 'image',
            'size': file_size,
            'dimensions': dimensions
        }
    
    # Check if it's a text file by trying to decode as UTF-8
    # We'll read a small portion to avoid huge files
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(1024)  # Read first 1KB for preview
            f.seek(0)
            # Check if entire file is valid UTF-8
            full_content = f.read()
            return {
                'type': 'text',
                'size': file_size,
                'content': full_content
            }
    except (UnicodeDecodeError, UnicodeError):
        raise ValueError(f"Unsupported file type: {filepath}")
