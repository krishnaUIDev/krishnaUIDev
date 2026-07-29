import io
import os
import requests
from PIL import Image

# ASCII character palettes ordered by luminance intensity
ASCII_CHARS_DARK = ["@", "%", "#", "*", "+", "=", "-", ":", ".", " "]
ASCII_CHARS_LIGHT = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]

def fetch_user_avatar(username: str, local_path: str = "avatar.png"):
    """
    Fetches user avatar image from local file or GitHub profile.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_local = os.path.join(base_dir, local_path)
    if os.path.exists(full_local):
        try:
            return Image.open(full_local)
        except Exception as e:
            print(f"Warning: Could not open local avatar {full_local}: {e}")

    url = f"https://github.com/{username}.png"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        print(f"Warning: Could not fetch avatar for {username}: {e}")
    return None

def escape_xml(text: str) -> str:
    """
    Escapes special XML characters for safe SVG embedding.
    """
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

def image_to_ascii_lines(image: Image.Image, width: int = 42, dark_mode: bool = True) -> list:
    """
    Converts a PIL image object into a list of ASCII text string lines.
    """
    if image is None:
        return []
    
    # Adjust for character aspect ratio in monospace fonts (~0.52 height/width ratio)
    aspect_ratio = image.height / image.width
    height = int(width * aspect_ratio * 0.50)
    height = max(15, min(height, 35)) # Keep bounding height reasonable for SVG layout
    
    # Convert image to grayscale
    grayscale_img = image.resize((width, height)).convert("L")
    pixels = grayscale_img.getdata()
    
    chars = ASCII_CHARS_DARK if dark_mode else ASCII_CHARS_LIGHT
    num_chars = len(chars)
    
    ascii_str = ""
    for pixel in pixels:
        index = min(num_chars - 1, int(pixel * num_chars / 256))
        ascii_str += chars[index]
        
    lines = []
    for i in range(0, len(ascii_str), width):
        lines.append(escape_xml(ascii_str[i:i + width]))
        
    return lines

def generate_ascii_svg_tspans(username: str, x: int = 20, start_y: int = 35, line_height: int = 18, width: int = 42, dark_mode: bool = True) -> str:
    """
    Fetches avatar and returns SVG <tspan> elements formatted for monospace font.
    """
    avatar = fetch_user_avatar(username)
    if not avatar:
        return f'<tspan x="{x}" y="{start_y}">[Avatar Unavailable]</tspan>'
        
    lines = image_to_ascii_lines(avatar, width=width, dark_mode=dark_mode)
    tspans = []
    current_y = start_y
    
    for line in lines:
        tspans.append(f'<tspan x="{x}" y="{current_y}">{line}</tspan>')
        current_y += line_height
        
    return "\n".join(tspans)
