"""Render Kerinol.C's profile banner with Pillow; no browser or network required.

Examples:
  py -3.13 generate_profile.py --source tools/avatar.png
  py -3.13 generate_profile.py --source portrait.jpg --portrait portrait-crt.png

The optional portrait is a prepared monochrome illustration. Without it, the
source image is converted deterministically into a small, stippled cell grid.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


WIDTH, HEIGHT = 800, 540
BACKGROUND = (5, 13, 8)
GREEN = (145, 245, 157)
BRIGHT = (204, 255, 193)
MUTED = (60, 114, 69)
COMMANDS = ("whoami", "open personal_archive", "keep_building()")
ASCII_LEVELS = " .,:;i1tfLCG08@"


def font_path(requested: str | None) -> str:
    if requested:
        return requested
    for candidate in (
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ):
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError("A monospace font is required; pass --font path/to/font.ttf")


def ascii_portrait(source: Image.Image) -> tuple[str, Image.Image]:
    """Use rectangular character cells, keeping the complete square composition."""
    gray = ImageOps.autocontrast(source.convert("L"), cutoff=1)
    gray = gray.filter(ImageFilter.GaussianBlur(0.6))
    grid = gray.resize((102, 51), Image.Resampling.BOX)
    lines = []
    for row in range(grid.height):
        lines.append("".join(ASCII_LEVELS[min(len(ASCII_LEVELS) - 1,
            grid.getpixel((col, row)) * len(ASCII_LEVELS) // 256)]
            for col in range(grid.width)))

    # Each 4x8 cell expresses the same tonal value using a deterministic pattern.
    art = Image.new("RGB", (408, 408), BACKGROUND)
    pixels = art.load()
    for row in range(grid.height):
        for col in range(grid.width):
            value = grid.getpixel((col, row))
            density = min(4, value // 52)
            color = (35 + value // 3, 65 + value * 3 // 4, 34 + value // 3)
            for yy in range(7):
                for xx in range(3):
                    rank = (xx + yy * 3) % 4
                    if rank < density:
                        pixels[col * 4 + xx, row * 8 + yy] = color
    return "\n".join(lines) + "\n", art


def prepared_portrait(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB").resize((408, 408), Image.Resampling.LANCZOS)
    tone = image.getchannel("G").point(lambda value: int(255 * (value / 255) ** 0.9))
    red = tone.point(lambda value: 5 + value * 48 // 255)
    green = tone.point(lambda value: 13 + value * 225 // 255)
    blue = tone.point(lambda value: 8 + value * 70 // 255)
    return Image.merge("RGB", (red, green, blue))


def base_screen(portrait: Image.Image, fonts: dict[str, ImageFont.FreeTypeFont]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((38, 26), "KERINOL.C / TERMINAL", font=fonts["small"], fill=MUTED)
    draw.text((651, 26), "PROFILE  /  01", font=fonts["small"], fill=MUTED)
    image.paste(portrait, (34, 54))
    x, y = 475, 88
    for label, value in (
        ("Name", "Kerinol.C"),
        ("Handle", "@yuzigewmy"),
        ("Interface", "terminal"),
        ("Mode", "build · learn · repeat"),
        ("Memory", "ideas in progress"),
    ):
        draw.text((x, y), label + ":", font=fonts["normal"], fill=BRIGHT)
        draw.text((x + 99, y), value, font=fonts["normal"], fill=GREEN)
        y += 29
    draw.line((x, 249, 758, 249), fill=(24, 62, 34), width=1)
    draw.text((x, 270), "Motto:", font=fonts["normal"], fill=BRIGHT)
    for row, line in enumerate(("while (true) {", "  keep_building();", "}")):
        draw.text((x, 300 + row * 26), line, font=fonts["normal"], fill=GREEN)
    draw.text((x, 404), "A PERSONAL CORNER", font=fonts["small"], fill=MUTED)
    colors = ((171, 73, 74), (95, 188, 113), (203, 185, 89), (102, 142, 183),
              (166, 120, 175), (95, 188, 183), (204, 223, 191), (103, 123, 107))
    for index, color in enumerate(colors):
        draw.rectangle((x + index * 25, 433, x + index * 25 + 21, 443), fill=color)
    draw.line((38, 476, 761, 476), fill=(24, 56, 31), width=1)
    return image


def crt_pass(image: Image.Image, vignette: Image.Image, mask: Image.Image) -> Image.Image:
    # Soft glow and fixed scanlines keep static content unchanged across frames.
    glow = image.filter(ImageFilter.GaussianBlur(1.6)).point(lambda value: value // 4)
    lit = ImageChops.add(image, glow)
    lit = ImageChops.multiply(lit, vignette)
    scanlines = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    scan = ImageDraw.Draw(scanlines)
    for row in range(18, HEIGHT - 18, 4):
        scan.line((18, row, WIDTH - 19, row), fill=(190, 190, 190), width=1)
    lit = ImageChops.multiply(lit, scanlines)
    frame = Image.new("RGB", (WIDTH, HEIGHT), (17, 24, 18))
    frame.paste(lit, (0, 0), mask)
    return frame


def frames_for_commands() -> list[tuple[str, bool, int]]:
    states = [("", True, 240)]
    for command in COMMANDS:
        states.extend((command[:length], True, 100) for length in range(1, len(command) + 1))
        states.extend((command, cursor, 280) for cursor in (False, True, False, True))
        states.extend((command[:length], True, 55) for length in range(len(command) - 1, -1, -1))
        states.append(("", True, 240))
    return states


def generate(args: argparse.Namespace) -> dict[str, object]:
    root = args.output.resolve()
    assets, tools = root / "assets", root / "tools"
    assets.mkdir(parents=True, exist_ok=True)
    tools.mkdir(parents=True, exist_ok=True)
    source = ImageOps.exif_transpose(Image.open(args.source)).convert("RGB")
    source.save(tools / "avatar.png")
    text, stippled = ascii_portrait(source)
    (assets / "avatar-ascii.txt").write_text(text, encoding="utf-8")
    portrait = prepared_portrait(args.portrait) if args.portrait else stippled
    face = font_path(args.font)
    fonts = {"normal": ImageFont.truetype(face, 16), "small": ImageFont.truetype(face, 12)}
    base = base_screen(portrait, fonts)
    mask = Image.new("L", (WIDTH, HEIGHT))
    ImageDraw.Draw(mask).rounded_rectangle((15, 15, 784, 524), radius=25, fill=255)
    # A wide elliptical falloff leaves portrait and type readable near the edges.
    shade = Image.new("L", (WIDTH, HEIGHT), 200)
    ImageDraw.Draw(shade).ellipse((-170, -110, 970, 650), fill=255)
    shade = shade.filter(ImageFilter.GaussianBlur(90))
    vignette = Image.merge("RGB", (shade, shade, shade))

    states = frames_for_commands()
    frames = []
    durations = []
    for command, cursor_on, duration in states:
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        prompt = "kerinol.c@local:~$ "
        draw.text((38, 489), prompt, font=fonts["normal"], fill=GREEN)
        draw.text((38 + draw.textlength(prompt, font=fonts["normal"]), 489),
                  command, font=fonts["normal"], fill=BRIGHT)
        if cursor_on:
            cursor_x = round(38 + draw.textlength(prompt + command, font=fonts["normal"])) + 2
            draw.rectangle((cursor_x, 491, cursor_x + 7, 506), fill=BRIGHT)
        frames.append(crt_pass(frame, vignette, mask))
        durations.append(duration)

    # A global palette and GIF frame deltas make the static portrait cheap.
    palette_source = Image.new("RGB", (WIDTH, HEIGHT + 48), BACKGROUND)
    palette_source.paste(frames[0], (0, 0))
    palette_draw = ImageDraw.Draw(palette_source)
    for index, color in enumerate(((171, 73, 74), (95, 188, 113), (203, 185, 89),
            (102, 142, 183), (166, 120, 175), (95, 188, 183), (204, 223, 191),
            (103, 123, 107))):
        palette_draw.rectangle((index * 100, HEIGHT, index * 100 + 99, HEIGHT + 47), fill=color)
    palette = palette_source.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    gif_path = assets / "neofetch.gif"
    indexed[0].save(gif_path, save_all=True, append_images=indexed[1:],
                    duration=durations, loop=0, optimize=True, disposal=1)
    full_command_index = next(i for i, state in enumerate(states) if state[0] == "whoami")
    frames[full_command_index].save(assets / "neofetch.png")

    decoded = Image.open(gif_path)
    total_duration = 0
    comparison = None
    decoded_frames = []
    for index in range(decoded.n_frames):
        decoded.seek(index)
        decoded.load()
        rgb = decoded.convert("RGB")
        assert rgb.size == (WIDTH, HEIGHT), (index, rgb.size)
        static = rgb.crop((0, 0, WIDTH, 478))
        if comparison is None:
            comparison = static
        else:
            assert ImageChops.difference(comparison, static).getbbox() is None, index
        total_duration += decoded.info.get("duration", 0)
        decoded_frames.append(rgb.copy())
    assert decoded.info.get("loop", 0) == 0
    assert ImageChops.difference(decoded_frames[0], decoded_frames[-1]).getbbox() is None
    assert gif_path.stat().st_size < 2_000_000
    assert ImageChops.difference(source, Image.open(tools / "avatar.png").convert("RGB")).getbbox() is None

    sampled_indices = (0, full_command_index, len(decoded_frames) // 3,
                       len(decoded_frames) // 2, len(decoded_frames) * 2 // 3,
                       len(decoded_frames) - 1)
    contact = Image.new("RGB", (WIDTH * 3, HEIGHT * 2), BACKGROUND)
    for slot, index in enumerate(sampled_indices):
        contact.paste(decoded_frames[index], ((slot % 3) * WIDTH, (slot // 3) * HEIGHT))
    contact.save(root / "contact-sheet.png")
    evidence = {
        "size": [WIDTH, HEIGHT],
        "source_size": list(source.size),
        "source_not_cropped": True,
        "avatar_pixel_identity": True,
        "source_frames": len(frames),
        "decoded_frames": len(decoded_frames),
        "loop": 0,
        "total_duration_ms": total_duration,
        "bytes": gif_path.stat().st_size,
        "all_frames_decoded": True,
        "static_profile_unchanged": True,
        "loop_seam_equal": True,
        "font": face,
        "portrait": str(args.portrait) if args.portrait else "deterministic stippled source",
    }
    (root / "verification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    script_root = Path(__file__).resolve().parent
    parser.add_argument("--source", type=Path, default=script_root / "avatar.png")
    parser.add_argument("--portrait", type=Path, help="Optional prepared CRT portrait")
    parser.add_argument("--font", help="Monospace TrueType font; defaults to Consolas on Windows")
    parser.add_argument("--output", type=Path, default=script_root.parent / "work" / "render")
    print(json.dumps(generate(parser.parse_args()), indent=2))
