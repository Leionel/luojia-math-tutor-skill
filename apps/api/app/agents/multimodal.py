"""
Multimodal Message Utilities
=============================

Converts plain-text messages + image attachments into the multimodal
message format expected by vision-capable LLMs.
"""

import base64
import re
from pathlib import Path
from typing import Any

MIME_FALLBACK = "image/png"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
_DATA_URL = re.compile(
    r"^data:(image/(?:png|jpeg|gif|webp));base64,([A-Za-z0-9+/=\r\n]+)$"
)
_UPLOAD_REFERENCE = re.compile(
    r"^/api/uploads/([0-9a-f-]{36}\.(?:png|jpg|jpeg|gif|webp))$",
    re.IGNORECASE,
)


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
    base64_image: str = "",
    mime_type: str = MIME_FALLBACK,
    provider: str = "openai",
    image_urls: list[str] | None = None,
) -> dict[str, Any]:
    """Format a message containing both text and image for the specified provider."""
    content_parts: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    
    if image_urls:
        content_parts.extend(
            build_openai_image_part(base64_data="", url=url)
            for url in image_urls
        )
    elif provider == "anthropic":
        content_parts.append(build_anthropic_image_part(base64_data=base64_image, mime_type=mime_type))
    else:
        content_parts.append(build_openai_image_part(base64_data=base64_image, mime_type=mime_type))
        
    return {
        "role": "user",
        "content": content_parts
    }


def normalize_image_reference(reference: str, upload_root: Path) -> str:
    """Return a provider-safe data URL without fetching arbitrary remote URLs."""
    data_match = _DATA_URL.fullmatch(reference.strip())
    if data_match:
        mime_type, encoded = data_match.groups()
        try:
            raw = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise ValueError("Invalid base64 image attachment.") from exc
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValueError("Image attachment exceeds 10MB.")
        return f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}"

    upload_match = _UPLOAD_REFERENCE.fullmatch(reference.strip())
    if not upload_match:
        raise ValueError(
            "Images must be uploaded through /api/uploads or supplied as a safe data URL."
        )
    root = upload_root.resolve()
    path = (root / upload_match.group(1)).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Image path escapes the upload directory.") from exc
    if not path.is_file():
        raise ValueError("Uploaded image was not found.")
    raw = path.read_bytes()
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Image attachment exceeds 10MB.")
    mime_type = guess_mime_type(path.name)
    return f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}"
