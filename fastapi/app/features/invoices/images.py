import warnings
from io import BytesIO
from typing import BinaryIO

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


class InvalidImageError(ValueError):
    """The image is empty, corrupt, or has an unsafe resolution."""


class UnsupportedImageError(InvalidImageError):
    """The image MIME type or actual format is unsupported or mismatched."""


class ImageTooLargeError(InvalidImageError):
    """The image exceeds the upload size limit."""


def read_invoice_image(file: BinaryIO, mime_type: str) -> tuple[bytes, str]:
    """Read and validate an image, always closing the input stream."""
    try:
        if mime_type not in IMAGE_FORMATS:
            raise UnsupportedImageError("Elige una imagen JPG, PNG o WEBP.")
        contents = file.read(MAX_IMAGE_BYTES + 1)
    finally:
        file.close()

    if not contents:
        raise InvalidImageError("La imagen está vacía.")
    if len(contents) > MAX_IMAGE_BYTES:
        raise ImageTooLargeError("La imagen no debe superar los 10 MB.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(contents)) as image:
                if image.format != IMAGE_FORMATS[mime_type]:
                    raise UnsupportedImageError("El formato de la imagen no coincide con el tipo de archivo enviado.")
                image.verify()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InvalidImageError("La resolución de la imagen es demasiado grande.") from exc
    except UnsupportedImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise InvalidImageError("No se pudo leer la imagen. Selecciona otro archivo.") from exc

    return contents, mime_type
