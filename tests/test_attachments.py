import pytest
import os
import tempfile
from attachments import process_attachment, get_image_dimensions


class TestProcessAttachment:
    def test_text_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello, world!")
            tmpname = f.name
        try:
            result = process_attachment(tmpname)
            assert result['type'] == 'text'
            assert result['size'] == 13
            assert result['content'] == "Hello, world!"
        finally:
            os.unlink(tmpname)

    def test_empty_text_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            tmpname = f.name
        try:
            result = process_attachment(tmpname)
            assert result['type'] == 'text'
            assert result['size'] == 0
            assert result['content'] == ""
        finally:
            os.unlink(tmpname)

    def test_png_image(self):
        # Create a minimal valid PNG (1x1 pixel)
        png_data = (
            b'\x89PNG\r\n\x1a\n'  # signature
            b'\x00\x00\x00\rIHDR'  # IHDR chunk header
            + struct.pack('>II', 1, 1)  # width=1, height=1
            + b'\x08\x02\x00\x00\x00'  # bit depth, color type, compression, filter, interlace
            + b'\x00\x00\x00\x00'  # CRC (dummy)
            + b'\x00\x00\x00\x00IEND'  # IEND chunk
            + b'\x00\x00\x00\x00'  # CRC (dummy)
        )
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(png_data)
            tmpname = f.name
        try:
            result = process_attachment(tmpname)
            assert result['type'] == 'image'
            assert result['size'] == len(png_data)
            assert result['dimensions'] == (1, 1)
        finally:
            os.unlink(tmpname)

    def test_jpeg_image(self):
        # Create a minimal valid JPEG (SOI + SOF0 with dimensions 2x2)
        # JPEG structure: SOI (FF D8), APP0?, DQT, SOF0, SOS, EOI
        # Minimal: just SOI, SOF0, SOS, EOI? Not valid but we only need to parse SOF0
        # We'll create a minimal header that matches our parser.
        jpeg_bytes = (
            b'\xff\xd8\xff\xe0' +  # SOI + APP0 marker
            b'\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00' +
            b'\xff\xc0' +  # SOF0 marker
            b'\x00\x0b' +  # length (11 bytes)
            b'\x08' +      # precision
            b'\x00\x02' +  # height = 2
            b'\x00\x02' +  # width = 2
            b'\x01' +      # number of components
            b'\x01\x11\x00' +  # component info
            b'\xff\xd9'    # EOI
        )
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(jpeg_bytes)
            tmpname = f.name
        try:
            result = process_attachment(tmpname)
            assert result['type'] == 'image'
            assert result['dimensions'] == (2, 2)
        finally:
            os.unlink(tmpname)

    def test_gif_image(self):
        # Minimal GIF89a (1x1 pixel)
        gif_data = (
            b'GIF89a'
            + struct.pack('<HH', 1, 1)  # width=1, height=1
            + b'\x00'  # packed fields (no global color table)
            + b'\x00'  # background color index
            + b'\x00'  # pixel aspect ratio
            + b'\x21\xf9\x04\x00\x00\x00\x00\x00'  # graphic control extension
            + b'\x2c\x00\x00\x00\x00'  # image descriptor
            + struct.pack('<HH', 1, 1)  # image width/height
            + b'\x00'  # packed fields
            + b'\x02'  # LZW min code size
            + b'\x02\x4c\x01'  # image data
            + b'\x00\x3b'  # trailer
        )
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
            f.write(gif_data)
            tmpname = f.name
        try:
            result = process_attachment(tmpname)
            assert result['type'] == 'image'
            assert result['dimensions'] == (1, 1)
        finally:
            os.unlink(tmpname)

    def test_bmp_image(self):
        # Minimal 24-bit BMP (1x1 pixel)
        # BMP header: 14 bytes, DIB header: 40 bytes, then pixel data
        width = 1
        height = 1
        row_size = ((width * 24 + 31) // 32) * 4  # 4 bytes
        pixel_data = b'\xff\x00\x00'  # blue pixel
        padding = b'\x00' * (row_size - 3)
        file_size = 14 + 40 + len(pixel_data) + len(padding)
        bmp_header = struct.pack('<HIHHII', 0x4D42, file_size, 0, 0, 54, 40)
        dib_header = struct.pack('<IiiHHIIiiII', 40, width, height, 1, 24, 0, 0, 0, 0, 0, 0)
        bmp_data = bmp_header + dib_header + pixel_data + padding
        with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as f:
            f.write(bmp_data)
            tmpname = f.name
        try:
            result = process_attachment(tmpname)
            assert result['type'] == 'image'
            assert result['dimensions'] == (1, 1)
        finally:
            os.unlink(tmpname)

    def test_unsupported_file_type(self):
        # Create a binary file that is not image nor text (e.g., random bytes)
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')
            tmpname = f.name
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                process_attachment(tmpname)
        finally:
            os.unlink(tmpname)

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            process_attachment("/nonexistent/path/file.txt")

    def test_large_text_file(self):
        # Test that large text file is fully read
        content = "A" * 10000
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            tmpname = f.name
        try:
            result = process_attachment(tmpname)
            assert result['type'] == 'text'
            assert result['size'] == 10000
            assert result['content'] == content
        finally:
            os.unlink(tmpname)


import struct  # needed for test helpers

class TestGetImageDimensions:
    def test_too_small_file(self):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            tmpname = f.name
        try:
            with pytest.raises(ValueError, match="File too small"):
                get_image_dimensions(tmpname)
        finally:
            os.unlink(tmpname)

    def test_invalid_png_no_ihdr(self):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00'*20)
            tmpname = f.name
        try:
            with pytest.raises(ValueError, match="missing IHDR"):
                get_image_dimensions(tmpname)
        finally:
            os.unlink(tmpname)
