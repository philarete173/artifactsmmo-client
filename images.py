import io

import requests

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    Image = None
    _PIL_AVAILABLE = False


CHAR_RAMP = ' .:-=+*#%@'
SKIN_IMAGE_URL = 'https://artifactsmmo.com/images/characters/{skin}.png'
DEFAULT_COLUMNS = 40
REQUEST_TIMEOUT = 5


def _to_ascii(image, columns=DEFAULT_COLUMNS):
    width, height = image.size
    aspect = height / width
    char_height = max(1, int(columns * aspect * 0.5))
    resized = image.resize((columns, char_height))
    gray = resized.convert('L')
    pixels = list(gray.getdata())
    ramp_size = len(CHAR_RAMP)
    lines = []

    for i in range(0, len(pixels), columns):
        row = pixels[i:i + columns]
        line = ''.join(CHAR_RAMP[min(p * ramp_size // 256, ramp_size - 1)] for p in row)
        lines.append(line)

    return '\n'.join(lines)


def _fetch_image(url):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def display_character_skin(skin):
    """Download and print an ASCII rendering of the character skin.

    Silently skips on missing skin code, missing Pillow, or any
    download/decode failure so the rest of the client keeps
    working when the optional image dependency is not installed
    or the image is unavailable."""

    if not skin or not _PIL_AVAILABLE:
        return

    try:
        image = _fetch_image(SKIN_IMAGE_URL.format(skin=skin))
    except (requests.RequestException, ValueError, OSError) as error:
        print(f'(Could not load skin image for {skin}: {error})')
        return

    print(_to_ascii(image))
