import io
import qrcode
from PIL import Image


def generate_qrcode(data: str, box_size=8, border=2) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def qrcode_to_bytes(data: str, box_size=8, border=2) -> bytes:
    img = generate_qrcode(data, box_size, border)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
