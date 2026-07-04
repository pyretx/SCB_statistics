"""Dev tool — generate the PNG logos from code (Pillow). Committed PNGs are what
Streamlit's st.image / page_icon use (they can't rasterise the SVGs). Rendered at
4× then downscaled with LANCZOS for smooth edges.

Outputs in assets/: logo.png (global globe), logo_sweden.png (blue-yellow-blue
bars), logo_france.png (blue-white-red bars).

Run:  python build_logos.py
"""
import math
import os

from PIL import Image, ImageDraw

HERE   = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
S      = 256          # final size
SS     = 4            # supersample factor


def _canvas():
    return Image.new("RGBA", (S * SS, S * SS), (0, 0, 0, 0))


def _bars(colors, outline=None):
    """Three ascending rounded bars. colors = (c1, c2, c3); outline per-bar list
    or None. Geometry matches the original brand mark."""
    img = _canvas()
    d = ImageDraw.Draw(img)
    geo = [(28, 130, 52, 90), (102, 90, 52, 130), (176, 40, 52, 180)]
    for (x, y, w, h), col, i in zip(geo, colors, range(3)):
        ol = outline[i] if outline else None
        d.rounded_rectangle(
            [x * SS, y * SS, (x + w) * SS, (y + h) * SS],
            radius=10 * SS, fill=col,
            outline=ol, width=3 * SS if ol else 0)
    return img.resize((S, S), Image.LANCZOS)


def _globe():
    """Blue globe with white meridian/parallel grid and a yellow equator."""
    img = _canvas()
    d = ImageDraw.Draw(img)
    cx = cy = 128 * SS
    r = 100 * SS
    blue, white, yellow = "#006AA7", "#FFFFFF", "#FECC00"
    lw = 4 * SS
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=blue)
    # meridians (vertical ellipses) + centre line
    for rx in (100, 60, 26):
        d.ellipse([cx - rx * SS, cy - r, cx + rx * SS, cy + r],
                  outline=white, width=lw)
    d.line([cx, cy - r, cx, cy + r], fill=white, width=lw)
    # parallels (horizontal chords of the circle)
    for dy in (45, 0, -45):
        half = math.sqrt((100 ** 2) - (dy ** 2)) * SS
        y = cy - dy * SS
        col = yellow if dy == 0 else white
        w = 6 * SS if dy == 0 else lw
        d.line([cx - half, y, cx + half, y], fill=col, width=w)
    return img.resize((S, S), Image.LANCZOS)


def save(img, name):
    p = os.path.join(ASSETS, name)
    img.save(p)
    print(f"wrote {name} ({os.path.getsize(p)} bytes)")


if __name__ == "__main__":
    save(_globe(), "logo.png")
    save(_bars(("#006AA7", "#FECC00", "#006AA7")), "logo_sweden.png")
    save(_bars(("#0055A4", "#FFFFFF", "#EF4135"),
               outline=[None, "#C8CCD4", None]), "logo_france.png")
