"""Image compression and processing utilities."""

import os
from pathlib import Path
from typing import Literal
from PIL import Image
import base64
from io import BytesIO


QualityLevel = Literal["high", "medium", "low"]
ImageFormat = Literal["png", "jpg"]


# Quality presets
QUALITY_PRESETS = {
    "high": {"max_size": 1500, "jpeg_quality": 90, "dpi": 200},
    "medium": {"max_size": 1024, "jpeg_quality": 85, "dpi": 150},
    "low": {"max_size": 768, "jpeg_quality": 75, "dpi": 100},
}


def compress_and_resize_image(
    image_path: str | Path,
    output_path: str | Path,
    quality: QualityLevel = "medium",
    image_format: ImageFormat = "jpg",
) -> dict:
    """
    Compress and resize an image to reduce token usage.

    Args:
        image_path: Path to input image
        output_path: Path to save compressed image
        quality: Quality level (high/medium/low)
        image_format: Output format (png/jpg)

    Returns:
        Dictionary with image metadata (width, height, file_size)
    """
    preset = QUALITY_PRESETS[quality]
    max_size = preset["max_size"]
    jpeg_quality = preset["jpeg_quality"]

    with Image.open(image_path) as img:
        # Convert RGBA to RGB for JPEG
        if image_format == "jpg" and img.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB" and image_format == "jpg":
            img = img.convert("RGB")

        # Resize if needed
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Save with appropriate settings
        save_kwargs = {}
        if image_format == "jpg":
            save_kwargs = {
                "format": "JPEG",
                "quality": jpeg_quality,
                "optimize": True,
            }
        else:
            save_kwargs = {
                "format": "PNG",
                "optimize": True,
            }

        img.save(output_path, **save_kwargs)

        # Get file size
        file_size = os.path.getsize(output_path)

        return {
            "width": img.width,
            "height": img.height,
            "file_size": file_size,
            "format": image_format.upper(),
        }


def image_to_base64(image_path: str | Path, quality: QualityLevel = "medium") -> str:
    """
    Convert image to base64 string with compression.

    Args:
        image_path: Path to image file
        quality: Quality level for compression

    Returns:
        Base64 encoded string
    """
    preset = QUALITY_PRESETS[quality]
    max_size = preset["max_size"]
    jpeg_quality = preset["jpeg_quality"]

    with Image.open(image_path) as img:
        # Convert for JPEG
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if needed
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=jpeg_quality, optimize=True)
        img_bytes = buffer.getvalue()

        return base64.b64encode(img_bytes).decode("utf-8")
