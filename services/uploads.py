from pathlib import Path
import secrets
from flask import abort, current_app


def save_image(upload, folder):
    if not upload or not upload.filename:
        abort(400,description='Choose an image to upload.')
    raw=upload.read(2*1024*1024+1)
    extension='.png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else '.jpg' if raw.startswith(b'\xff\xd8\xff') else '.webp' if raw[:4]==b'RIFF' and raw[8:12]==b'WEBP' else None
    if not extension or len(raw)>2*1024*1024:
        abort(400,description='Use a PNG, JPEG or WebP image of up to 2 MB.')
    name=secrets.token_hex(16)+extension
    destination=Path(current_app.static_folder)/folder
    destination.mkdir(parents=True,exist_ok=True)
    (destination/name).write_bytes(raw)
    return name
