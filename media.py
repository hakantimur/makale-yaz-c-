import base64
import os


def save_image_bytes(image_bytes: bytes, slug: str, filename: str, output_dir: str = "outputs/images") -> str:
    """Saves generated image/chart bytes under outputs/images/<slug>/<filename> and
    returns the saved path. Kept as a local backup copy — the markdown/HTML output embeds
    the image as a base64 data URI instead (see image_bytes_to_data_uri), since a relative
    file path would be a broken link both in the Streamlit preview and once pasted into a
    CMS like Wagtail, which don't serve this app's local folder."""
    folder = os.path.join(output_dir, slug)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path


def image_bytes_to_data_uri(image_bytes: bytes, mime: str = "image/png") -> str:
    """Encodes image bytes as a self-contained base64 data URI, so the <img> tag works
    anywhere the HTML is pasted, with no separate file hosting/upload step required."""
    b64 = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"
