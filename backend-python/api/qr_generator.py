"""
QR code generation for share links.
"""

import io
import qrcode
from qrcode.image import svg
from fastapi import Response


def generate_qr_code(
    data: str,
    size: int = 10,
    border: int = 4,
    error_correction: int = qrcode.constants.ERROR_CORRECT_M,
) -> bytes:
    """
    Generate QR code image as PNG bytes.

    Args:
        data: Data to encode in QR code
        size: Box size (pixels per module)
        border: Border size (modules)
        error_correction: Error correction level

    Returns:
        PNG image bytes
    """
    qr_code_instance = qrcode.QRCode(
        version=1,
        error_correction=error_correction,
        box_size=size,
        border=border,
    )
    qr_code_instance.add_data(data)
    qr_code_instance.make(fit=True)

    qr_image = qr_code_instance.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    image_bytes_buffer = io.BytesIO()
    qr_image.save(image_bytes_buffer, format="PNG")
    image_bytes_buffer.seek(0)

    return image_bytes_buffer.read()


def generate_qr_response(data: str, **kwargs) -> Response:
    """
    Generate QR code and return as FastAPI Response.

    Args:
        data: Data to encode
        **kwargs: Additional arguments for generate_qr_code

    Returns:
        FastAPI Response with PNG image
    """
    qr_code_bytes = generate_qr_code(data, **kwargs)
    return Response(content=qr_code_bytes, media_type="image/png")


def generate_svg_qr_code(data: str, **kwargs) -> str:
    """
    Generate QR code as SVG string.

    Args:
        data: Data to encode
        **kwargs: Additional arguments

    Returns:
        SVG string
    """
    qr_code_instance = qrcode.QRCode(
        version=1,
        error_correction=kwargs.get("error_correction", qrcode.constants.ERROR_CORRECT_M),
        box_size=kwargs.get("size", 10),
        border=kwargs.get("border", 4),
    )
    qr_code_instance.add_data(data)
    qr_code_instance.make(fit=True)

    # Use SVG factory
    svg_image_factory = svg.SvgImage
    svg_image = qr_code_instance.make_image(image_factory=svg_image_factory)

    # Convert to string
    svg_bytes_buffer = io.BytesIO()
    svg_image.save(svg_bytes_buffer)
    svg_bytes_buffer.seek(0)

    return svg_bytes_buffer.read().decode("utf-8")
