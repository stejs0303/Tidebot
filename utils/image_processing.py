from PIL import Image as _Image 
from PIL import ImageDraw as _ImageDraw
from PIL.Image import Resampling as _Resampling


def round_corner(radius, fill):
    """Draw a round corner"""
    corner = _Image.new('RGBA', (radius, radius), 0x00000000)
    draw = _ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
    return corner


def round_rectangle(size, radius, fill):
    """Draw a rounded rectangle"""
    width, height = size
    rectangle = _Image.new('RGBA', size, fill)
    corner = round_corner(radius, fill)
    rectangle.paste(corner, (0, 0))
    rectangle.paste(corner.rotate(90), (0, height - radius))  # Rotate the corner and paste it
    rectangle.paste(corner.rotate(180), (width - radius, height - radius))
    rectangle.paste(corner.rotate(270), (width - radius, 0))
    return rectangle


def resize_and_save(img: _Image.Image, img_path: str, size: tuple):
    img = img.resize(size, _Resampling.BICUBIC)
    img.save(img_path)