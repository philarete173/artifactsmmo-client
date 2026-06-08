import io

import requests

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    Image = None
    _PIL_AVAILABLE = False


CHAR_RAMP = ' .:-=+*#%@'
DEFAULT_COLUMNS = 40
REQUEST_TIMEOUT = 5
IMAGE_URL_TEMPLATE = 'https://artifactsmmo.com/images/{category}/{key}.png'


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


def display_image(category, key):
    """Download and print an ASCII rendering of an image from the game API.

    Args:
        category: image category from ImageCategoryEnum (e.g. 'characters', 'maps')
        key: image identifier (e.g. skin name, map name)

    Silently skips if Pillow is not installed or on any
    download/decode failure so the rest of the client keeps
    working when the optional image dependency is not available.
    """

    if not key or not _PIL_AVAILABLE:
        return

    url = IMAGE_URL_TEMPLATE.format(category=category, key=key)

    try:
        image = _fetch_image(url)
    except (requests.RequestException, ValueError, OSError) as error:
        print(f'(Could not load {category} image for {key}: {error})')
        return

    print(f'{_to_ascii(image)}\n')
