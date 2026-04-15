from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "controller" / "assets" / "fren-office-sheet.png"
DEFAULT_OUTDIR = ROOT / "controller" / "assets" / "generated"
DEFAULT_MANIFEST = DEFAULT_OUTDIR / "office-sprite-manifest.json"
TARGET_BOX = (220, 190)
PADDING = 12


@dataclass(frozen=True)
class Clip:
    x: int
    y: int
    w: int
    h: int


ANIMATIONS: dict[str, dict[str, object]] = {
    "ready": {
        "interval_ms": 180,
        "sequence": [0, 0, 1, 2, 3, 3, 2, 1],
        "clips": [
            Clip(650, 24, 320, 300),
            Clip(985, 24, 320, 300),
            Clip(1300, 24, 320, 300),
            Clip(1620, 24, 320, 300),
        ],
    },
    "working": {
        "interval_ms": 120,
        "sequence": [0, 1, 2, 3, 2, 1],
        "clips": [
            Clip(700, 300, 440, 300),
            Clip(1080, 300, 400, 300),
            Clip(1425, 300, 400, 300),
            Clip(1750, 300, 380, 300),
        ],
    },
    "booting": {
        "interval_ms": 145,
        "sequence": [0, 1, 2, 3, 2, 1],
        "clips": [
            Clip(790, 560, 270, 290),
            Clip(1060, 560, 270, 290),
            Clip(1320, 540, 330, 310),
            Clip(1660, 560, 270, 290),
        ],
    },
    "broken": {
        "interval_ms": 220,
        "sequence": [0, 1, 2, 3, 2, 1],
        "clips": [
            Clip(730, 810, 340, 320),
            Clip(1040, 810, 340, 320),
            Clip(1350, 810, 340, 320),
            Clip(1660, 810, 340, 320),
        ],
    },
    "dead": {
        "interval_ms": 520,
        "sequence": [0, 1, 2, 3, 2, 1],
        "clips": [
            Clip(870, 1090, 240, 270),
            Clip(1120, 1090, 240, 270),
            Clip(1360, 1090, 240, 270),
            Clip(1610, 1090, 240, 270),
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build normalized office sprite frames for controller Office View.")
    parser.add_argument("--image", type=Path, default=DEFAULT_SOURCE, help="Source sprite sheet path")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR, help="Output directory for generated frames")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Manifest JSON output path")
    return parser.parse_args()


def is_edge_whitespace(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    if alpha < 8:
        return True
    brightest = max(red, green, blue)
    darkest = min(red, green, blue)
    return brightest >= 245 and darkest >= 235 and brightest - darkest <= 18


def clear_edge_whitespace(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        if not (0 <= x < width and 0 <= y < height):
            return
        key = (x, y)
        if key in visited:
            return
        visited.add(key)
        if not is_edge_whitespace(pixels[x, y]):
            return
        queue.append((x, y))

    for x in range(width):
        push(x, 0)
        push(x, height - 1)
    for y in range(height):
        push(0, y)
        push(width - 1, y)

    while queue:
        x, y = queue.popleft()
        red, green, blue, _ = pixels[x, y]
        pixels[x, y] = (red, green, blue, 0)
        push(x + 1, y)
        push(x - 1, y)
        push(x, y + 1)
        push(x, y - 1)
    return rgba


def trim_alpha(image: Image.Image, pad: int = 4) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return image
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(image.width, right + pad)
    bottom = min(image.height, bottom + pad)
    return image.crop((left, top, right, bottom))


def extract_frame(sheet: Image.Image, clip: Clip) -> Image.Image:
    canvas = Image.new("RGBA", (clip.w + PADDING * 2, clip.h + PADDING * 2), (0, 0, 0, 0))
    cropped = sheet.crop((clip.x, clip.y, clip.x + clip.w, clip.y + clip.h)).convert("RGBA")
    canvas.paste(cropped, (PADDING, PADDING))
    trimmed = trim_alpha(clear_edge_whitespace(canvas))
    return trimmed


def normalize_frames(frames: list[Image.Image]) -> tuple[list[Image.Image], tuple[int, int]]:
    viewport_width = max(frame.width for frame in frames)
    viewport_height = max(frame.height for frame in frames)
    scale = min(
        TARGET_BOX[0] / viewport_width,
        TARGET_BOX[1] / viewport_height,
        1.0,
    )
    render_size = (max(1, round(viewport_width * scale)), max(1, round(viewport_height * scale)))
    normalized: list[Image.Image] = []
    for frame in frames:
        if scale != 1.0:
            resized = frame.resize(
                (max(1, round(frame.width * scale)), max(1, round(frame.height * scale))),
                Image.Resampling.NEAREST,
            )
        else:
            resized = frame
        canvas = Image.new("RGBA", TARGET_BOX, (0, 0, 0, 0))
        draw_x = round((TARGET_BOX[0] - resized.width) / 2)
        draw_y = TARGET_BOX[1] - resized.height
        canvas.paste(resized, (draw_x, draw_y), resized)
        normalized.append(canvas)
    return normalized, render_size


def write_manifest(manifest_path: Path, source: Path, states: dict[str, dict[str, object]]) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "frame_box": {"width": TARGET_BOX[0], "height": TARGET_BOX[1]},
        "states": states,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_assets(source: Path, outdir: Path, manifest_path: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"source sprite sheet not found: {source}")

    outdir.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(source).convert("RGBA")
    manifest_states: dict[str, dict[str, object]] = {}

    for state_name, config in ANIMATIONS.items():
        clips = list(config["clips"])
        raw_frames = [extract_frame(sheet, clip) for clip in clips]
        normalized_frames, render_size = normalize_frames(raw_frames)
        frame_entries = []
        for idx, frame in enumerate(normalized_frames):
            filename = f"{state_name}-{idx:02d}.png"
            path = outdir / filename
            frame.save(path)
            frame_entries.append(
                {
                    "src": f"/controller-assets/generated/{filename}",
                    "width": render_size[0],
                    "height": render_size[1],
                }
            )
        manifest_states[state_name] = {
            "interval_ms": int(config["interval_ms"]),
            "sequence": list(config["sequence"]),
            "frames": frame_entries,
        }

    write_manifest(manifest_path, source, manifest_states)


def main() -> None:
    args = parse_args()
    build_assets(args.image, args.outdir, args.manifest)
    print(f"generated office sprite assets in {args.outdir}")
    print(f"manifest: {args.manifest}")


if __name__ == "__main__":
    main()
