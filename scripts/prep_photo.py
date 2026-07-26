"""
Prepare a portrait photo for clean ASCII conversion:
  1. remove the background (rembg) so the subject is isolated
  2. auto-frame: crop to the subject and pad out to a square canvas, so the
     100x53 char grid always gets the same head-in-frame proportions no
     matter how the source photo happened to be cropped
  3. boost LOCAL contrast (CLAHE) so a flatly-lit face gains highlights and
     shadows -- this is what turns a dark blob into a recognizable face
  4. composite the subject onto pure white so the background reads as blank
     (white -> spaces in the ascii ramp)

Output: source-prepped.png (grayscale), consumed by make_hero_svg.py.
Run once whenever the source photo changes; the ascii SVG itself is static.

    python scripts/prep_photo.py <input.jpg> [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

MARGIN = 0.06   # padding around the subject, as a fraction of the square side

# 1. cut out the subject
cut = remove(Image.open(INP).convert("RGBA"))
rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])                 # 0 = background

# 2. auto-frame: square canvas around the subject's bounding box. the ascii
#    grid is effectively square, so a non-square source would otherwise get
#    stretched -- and a loosely-cropped photo would waste rows on empty space.
ys, xs = np.nonzero(alpha > 8)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
side = int(max(y1 - y0, x1 - x0) * (1 + 2 * MARGIN))
cy, cx = (y0 + y1) // 2, (x0 + x1) // 2

sq_rgb = np.zeros((side, side, 3), np.uint8)
sq_alpha = np.zeros((side, side), np.uint8)
# source window, clipped to the image; then the matching destination window
sy0, sy1 = max(0, cy - side // 2), min(rgb.shape[0], cy - side // 2 + side)
sx0, sx1 = max(0, cx - side // 2), min(rgb.shape[1], cx - side // 2 + side)
dy0, dx0 = sy0 - (cy - side // 2), sx0 - (cx - side // 2)
sq_rgb[dy0:dy0 + sy1 - sy0, dx0:dx0 + sx1 - sx0] = rgb[sy0:sy1, sx0:sx1]
sq_alpha[dy0:dy0 + sy1 - sy0, dx0:dx0 + sx1 - sx0] = alpha[sy0:sy1, sx0:sx1]
rgb, alpha = sq_rgb, sq_alpha

# 3. local-contrast the luminance (CLAHE)
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
gray = clahe.apply(gray)

# a touch of global lift so the face sits in the sparse end of the ramp
gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)

# 3. paste onto white using the alpha mask (feathered a hair to avoid a halo)
mask = (alpha.astype(np.float32) / 255.0)
mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
out = gray.astype(np.float32) * mask + 255.0 * (1.0 - mask)
out = np.clip(out, 0, 255).astype(np.uint8)

Image.fromarray(out, mode="L").save(OUT)
print("wrote", OUT, out.shape)
