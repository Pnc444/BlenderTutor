import mss
import base64
from PIL import Image
from io import BytesIO


def screen_capture_image(monitor_index=1):
    """Return the current screenshot as RGB (for hashing / vision)."""
    with mss.MSS() as sct:
        # [0] is all monitors; 1..N are individual displays.
        screenshot = sct.grab(sct.monitors[monitor_index])
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")


def screen_capture():
    img = screen_capture_image(monitor_index=1)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def encode_image(buffer):
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return encoded


if __name__ == "__main__":
    buffer = screen_capture()
    encoded = encode_image(buffer)
    print(encoded[:100])  # just print the first 100 characters






 











