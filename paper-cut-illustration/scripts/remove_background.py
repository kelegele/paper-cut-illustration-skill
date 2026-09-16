# /// script
# requires-python = ">=3.10"
# dependencies = ["Pillow>=10,<13"]
# ///
"""Remove a deliberately flat color backdrop; no AI service or model download."""
import argparse
import json
from collections import deque
from pathlib import Path
from PIL import Image, ImageOps

def cutout(image, key, tolerance=35, feather=65, seeds=()):
    if len(key) != 3 or any(not 0 <= c <= 255 for c in key):
        raise ValueError("key must contain three RGB values in 0..255")
    if tolerance < 0 or feather <= 0 or tolerance + feather > 255:
        raise ValueError("require tolerance >= 0, feather > 0, sum <= 255")
    src = image.convert("RGBA")
    w, h = src.size
    pixels = list(src.get_flattened_data() if hasattr(src, "get_flattened_data") else src.getdata())
    distances = [max(abs(p[c] - key[c]) for c in range(3)) for p in pixels]
    limit = tolerance + feather
    visited = bytearray(w * h)
    queue = deque()
    def start(index):
        if not visited[index] and (distances[index] <= tolerance or pixels[index][3] == 0):
            visited[index] = 1
            queue.append(index)
    for x in range(w):
        start(x)
        start((h - 1) * w + x)
    for y in range(h):
        start(y * w)
        start(y * w + w - 1)
    if not queue:
        raise ValueError("No matching border background; use a flat-key source and correct key")
    for x, y in seeds:
        if not (0 <= x < w and 0 <= y < h):
            raise ValueError("seed outside image")
        index = y * w + x
        if distances[index] > tolerance and pixels[index][3] != 0:
            raise ValueError("seed does not match background color")
        start(index)
    while queue:
        i = queue.popleft()
        x, y = i % w, i // w
        neighbors = []
        if x: neighbors.append(i - 1)
        if x + 1 < w: neighbors.append(i + 1)
        if y: neighbors.append(i - w)
        if y + 1 < h: neighbors.append(i + w)
        for j in neighbors:
            if not visited[j] and (distances[j] < limit or pixels[j][3] == 0):
                visited[j] = 1
                queue.append(j)
    out = []
    for i, p in enumerate(pixels):
        if not visited[i]:
            out.append(p)
            continue
        factor = max(0.0, min(1.0, (distances[i] - tolerance) / feather))
        alpha = round(p[3] * factor)
        if alpha == 0:
            out.append((0, 0, 0, 0))
        else:
            # Reverse approximate compositing against the known key at soft edges.
            coverage = max(abs(p[c] - key[c]) / max(key[c], 255 - key[c]) for c in range(3))
            unmix = max(1 / 255, min(factor, coverage))
            rgb = tuple(round(max(0, min(255, (p[c] - (1 - unmix) * key[c]) / unmix))) for c in range(3))
            out.append((*rgb, alpha))
    result = Image.new("RGBA", src.size)
    result.putdata(out)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--key", required=True, help="Background hex color, e.g. #00FF00")
    parser.add_argument("--tolerance", type=int, default=35)
    parser.add_argument("--feather", type=int, default=65)
    parser.add_argument("--seed", action="append", default=[], help="Confirmed enclosed background pixel x,y; repeatable")
    args = parser.parse_args()
    try:
        raw = args.key.lstrip("#")
        if len(raw) != 6:
            raise ValueError("key must be #RRGGBB")
        key = tuple(int(raw[i:i+2], 16) for i in (0, 2, 4))
        seeds = [tuple(map(int, s.split(","))) for s in args.seed]
        if any(len(s) != 2 for s in seeds):
            raise ValueError("seeds must be x,y")
        if args.input.resolve() == args.output.resolve() or args.output.exists():
            raise ValueError("output must be a new path; source and existing outputs are never overwritten")
        if args.output.suffix.lower() != ".png":
            raise ValueError("output must end in .png")
        with Image.open(args.input) as im:
            result = cutout(ImageOps.exif_transpose(im), key, args.tolerance, args.feather, seeds)
        alpha = result.getchannel("A")
        lo, hi = alpha.getextrema()
        if lo != 0 or hi == 0:
            raise ValueError("invalid cutout: requires transparent background and remaining visible foreground")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            result.save(stream, format="PNG")
        with Image.open(args.output) as saved:
            assert saved.format == "PNG" and saved.mode == "RGBA"
            assert saved.size == result.size
        hist = alpha.histogram()
        print(json.dumps({"output": str(args.output.resolve()), "size": result.size,
                          "mode": "RGBA", "transparent_pixels": hist[0],
                          "visible_pixels": sum(hist[1:]),
                          "note": "Inspect on light/dark backgrounds; enclosed holes need explicit seeds."}))
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + "\n")

if __name__ == "__main__":
    main()
