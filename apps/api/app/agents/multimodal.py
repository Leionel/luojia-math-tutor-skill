"""
Multimodal Message Utilities
=============================

Converts plain-text messages + image attachments into the multimodal
message format expected by vision-capable LLMs.
"""

from typing import Any

MIME_FALLBACK = "image/png"


def guess_mime_type(filename: str, fallback: str = MIME_FALLBACK) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }.get(ext, fallback)


def build_openai_image_part(
    base64_data: str,
    mime_type: str = MIME_FALLBACK,
    url: str = "",
) -> dict[str, Any]:
    if url:
        image_url = url
    else:
        # Strip data URL prefix if accidentally included
        if base64_data.startswith("data:"):
            image_url = base64_data
        else:
            image_url = f"data:{mime_type};base64,{base64_data}"
    return {"type": "image_url", "image_url": {"url": image_url}}


def build_anthropic_image_part(
    base64_data: str,
    mime_type: str = MIME_FALLBACK,
) -> dict[str, Any]:
    # Strip data prefix if present
    if base64_data.startswith("data:"):
        base64_data = base64_data.split(",", 1)[-1]
        
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": mime_type,
            "data": base64_data,
        },
    }


def format_vision_message(
    prompt: str,
    base64_image: str,
    mime_type: str = MIME_FALLBACK,
    provider: str = "openai"
) -> dict[str, Any]:
    """Format a message containing both text and image for the specified provider."""
    content_parts: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    
    if provider == "anthropic":
        content_parts.append(build_anthropic_image_part(base64_data=base64_image, mime_type=mime_type))
    else:
        content_parts.append(build_openai_image_part(base64_data=base64_image, mime_type=mime_type))
        
    return {
        "role": "user",
        "content": content_parts
    }
