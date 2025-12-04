"""
QR code generation for share links.
"""
import io
from typing import Optional
import qrcode
from qrcode.image.pil import PilImage
from qrcode.image import svg
from fastapi import Response


def generate_qr_code(
    data: str,
    size: int = 10,
    border: int = 4,
    error_correction: int = qrcode.constants.ERROR_CORRECT_M
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
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_correction,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.read()


def generate_qr_response(data: str, **kwargs) -> Response:
    """
    Generate QR code and return as FastAPI Response.
    
    Args:
        data: Data to encode
        **kwargs: Additional arguments for generate_qr_code
        
    Returns:
        FastAPI Response with PNG image
    """
    qr_bytes = generate_qr_code(data, **kwargs)
    return Response(content=qr_bytes, media_type="image/png")


def generate_svg_qr_code(data: str, **kwargs) -> str:
    """
    Generate QR code as SVG string.
    
    Args:
        data: Data to encode
        **kwargs: Additional arguments
        
    Returns:
        SVG string
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=kwargs.get('error_correction', qrcode.constants.ERROR_CORRECT_M),
        box_size=kwargs.get('size', 10),
        border=kwargs.get('border', 4),
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Use SVG factory
    factory = svg.SvgImage
    img = qr.make_image(image_factory=factory)
    
    # Convert to string
    svg_bytes = io.BytesIO()
    img.save(svg_bytes)
    svg_bytes.seek(0)
    
    return svg_bytes.read().decode('utf-8')

