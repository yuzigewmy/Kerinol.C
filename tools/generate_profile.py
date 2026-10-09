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
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


WIDTH, HEIGHT = 800, 540
BACKGROUND = (5, 13, 8)
GREEN = (145, 245, 157)
BRIGHT = (204, 255, 193)
MUTED = (60, 114, 69)
COMMANDS = ("whoami", "open personal_archive", "keep_building()")
ASCII_LEVELS = " .,:;i1tfLCG08@"
PROFILE_ROWS = (("Name", "Kerinol.C"), ("Handle", "@yuzigewmy"),
                ("Interface", "terminal"), ("Mode", "build · learn · repeat"),
                ("Memory", "ideas in progress"))
MOTTO_LINES = ("while (true) {", "  keep_building();", "}")


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


def animated_portrait(portrait: Image.Image, phase: float) -> Image.Image:
    """Keep the image edges fixed while hair tips sway and the figure breathes."""
    width, height = portrait.size
    progress = phase / math.tau
    glint = (progress - 0.28) / 0.16
    image = portrait
    if 0 < glint < 1:
        lenses = Image.new("L", portrait.size)
        draw = ImageDraw.Draw(lenses)
        draw.polygon(((143, 181), (154, 178), (181, 180), (191, 185),
                      (196, 194), (190, 205), (175, 210), (151, 207), (145, 198)), fill=255)
        draw.polygon(((224, 181), (237, 178), (258, 181), (269, 187),
                      (274, 199), (267, 210), (250, 213), (230, 208), (224, 198)), fill=255)
        shine = Image.new("L", portrait.size)
        center = 127 + 166 * glint
        ImageDraw.Draw(shine).polygon(((center - 7, 169), (center + 7, 169),
            (center - 5, 222), (center - 19, 222)), fill=round(40 * math.sin(math.pi * glint)))
        shine = ImageChops.multiply(shine.filter(ImageFilter.GaussianBlur(2)), lenses)
        image = ImageChops.add(portrait, Image.merge("RGB", (
            shine.point(lambda value: value // 2), shine, shine.point(lambda value: value // 3))))

    def source_point(x: int, y: int) -> tuple[float, float]:
        edge = max(0, min(1, x / 20, (width - x) / 20, y / 20, (height - y) / 20))
        hair = max(0, min(1, (185 - y) / 125))
        wind = 5.5 * math.sin(phase * 2) + 1.2 * math.sin(phase * 4)
        dx = edge * (0.6 * math.sin(phase * 3) + hair * wind)
        dy = edge * (1.6 * math.sin(phase * 3) + hair * 1.2 * math.sin(phase * 2))
        return x - dx, y - dy

    mesh = []
    for y in range(0, height, 24):
        for x in range(0, width, 24):
            right, bottom = min(x + 24, width), min(y + 24, height)
            corners = (source_point(x, y), source_point(x, bottom),
                       source_point(right, bottom), source_point(right, y))
            mesh.append(((x, y, right, bottom), tuple(value for point in corners for value in point)))
    return image.transform(portrait.size, Image.Transform.MESH, mesh,
                           resample=Image.Resampling.BICUBIC)


def base_screen(portrait: Image.Image, fonts: dict[str, ImageFont.FreeTypeFont]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((38, 26), "KERINOL.C / TERMINAL", font=fonts["small"], fill=MUTED)
    draw.text((651, 26), "PROFILE  /  01", font=fonts["small"], fill=MUTED)
    image.paste(portrait, (34, 54))
    x, y = 475, 88
    for label, value in PROFILE_ROWS:
        draw.text((x, y), label + ":", font=fonts["normal"], fill=BRIGHT)
        draw.text((x + 99, y), value, font=fonts["normal"], fill=GREEN)
        y += 29
    draw.line((x, 249, 758, 249), fill=(24, 62, 34), width=1)
    draw.text((x, 270), "Motto:", font=fonts["normal"], fill=BRIGHT)
    for row, line in enumerate(MOTTO_LINES):
        draw.text((x, 300 + row * 26), line, font=fonts["normal"], fill=GREEN)
    draw.text((x, 404), "A PERSONAL CORNER", font=fonts["small"], fill=MUTED)
    colors = ((171, 73, 74), (95, 188, 113), (203, 185, 89), (102, 142, 183),
              (166, 120, 175), (95, 188, 183), (204, 223, 191), (103, 123, 107))
    for index, color in enumerate(colors):
        draw.rectangle((x + index * 25, 433, x + index * 25 + 21, 443), fill=color)
    draw.line((38, 476, 761, 476), fill=(24, 56, 31), width=1)
    return image


def animate_profile_text(image: Image.Image, fonts: dict[str, ImageFont.FreeTypeFont],
                         elapsed_ms: int) -> None:
    """Hold the complete profile, fade it out, then type each row in place."""
    if elapsed_ms < 1200:
        return
    draw = ImageDraw.Draw(image)
    for box in ((470, 82, 774, 237), (470, 268, 774, 379), (470, 400, 774, 422)):
        draw.rectangle(box, fill=BACKGROUND)
    lines = [((475, 88 + row * 29, label + ":", "normal", BRIGHT),
              (574, 88 + row * 29, value, "normal", GREEN))
             for row, (label, value) in enumerate(PROFILE_ROWS)]
    lines.append(((475, 270, "Motto:", "normal", BRIGHT),))
    lines.extend(((475, 300 + row * 26, line, "normal", GREEN),)
                 for row, line in enumerate(MOTTO_LINES))
    lines.append(((475, 404, "A PERSONAL CORNER", "small", MUTED),))
    fading = elapsed_ms < 1500
    intensity = max(0, (1500 - elapsed_ms) / 300) if fading else 1
    remaining = elapsed_ms - 1600
    for segments in lines:
        length = sum(len(segment[2]) for segment in segments)
        duration = length * 30 + 120
        visible = length if fading else max(0, min(length, remaining // 30))
        active = not fading and 0 <= remaining < duration
        cursor = None
        for x, y, text, font_key, color in segments:
            prefix = text[:visible]
            fill = tuple(round(bg + (fg - bg) * intensity)
                         for bg, fg in zip(BACKGROUND, color))
            draw.text((x, y), prefix, font=fonts[font_key], fill=fill)
            if visible <= len(text):
                cursor = (round(x + draw.textlength(prefix, font=fonts[font_key])), y, font_key)
                break
            visible -= len(text)
        if active and cursor and elapsed_ms // 300 % 2 == 0:
            x, y, font_key = cursor
            height = 11 if font_key == "small" else 15
            draw.rectangle((x + 2, y + 2, x + 7, y + height), fill=BRIGHT)
        remaining -= duration


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

    command_states = frames_for_commands()
    total_ms = sum(duration // 10 * 10 for _, _, duration in command_states)
    states = []
    command_index, command_end = 0, command_states[0][2] // 10 * 10
    for elapsed in range(0, total_ms, 100):
        while elapsed >= command_end and command_index < len(command_states) - 1:
            command_index += 1
            command_end += command_states[command_index][2] // 10 * 10
        command, cursor_on, _ = command_states[command_index]
        states.append((command, cursor_on, min(100, total_ms - elapsed)))
    frames = []
    durations = []
    elapsed_ms = 0
    for command, cursor_on, duration in states:
        frame = base.copy()
        phase = math.tau * elapsed_ms / total_ms
        frame.paste(animated_portrait(portrait, phase), (34, 54))
        animate_profile_text(frame, fonts, elapsed_ms)
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
        elapsed_ms += duration
    frames.append(frames[0].copy())
    durations.append(100)

    # The first frame contains the full profile, keeping its global palette stable.
    palette_source = Image.new("RGB", (WIDTH, HEIGHT + 48), BACKGROUND)
    palette_source.paste(frames[0], (0, 0))
    palette_draw = ImageDraw.Draw(palette_source)
    for index, color in enumerate(((171, 73, 74), (95, 188, 113), (203, 185, 89),
            (102, 142, 183), (166, 120, 175), (95, 188, 183), (204, 223, 191),
            (103, 123, 107))):
        palette_draw.rectangle((index * 100, HEIGHT, index * 100 + 99, HEIGHT + 47), fill=color)
    palette = palette_source.quantize(colors=48, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    gif_path = assets / "neofetch.gif"
    indexed[0].save(gif_path, save_all=True, append_images=indexed[1:],
                    duration=durations, loop=0, optimize=True, disposal=1)
    portrait_frames = [frame.crop((34, 54, 442, 462)) for frame in indexed]
    portrait_frames[0].save(assets / "portrait-crt.gif", save_all=True,
        append_images=portrait_frames[1:], duration=durations, loop=0, optimize=True, disposal=1)
    full_command_index = next(i for i, state in enumerate(states) if state[0] == "whoami")
    # The reduced-motion fallback always displays every profile line.
    static_frame = frames[full_command_index].copy()
    static_frame.paste(crt_pass(base, vignette, mask).crop((467, 54, 770, 462)), (467, 54))
    static_frame.save(assets / "neofetch.png")
    assert ImageChops.difference(Image.open(assets / "neofetch.png").crop((467, 54, 770, 462)),
                                crt_pass(base, vignette, mask).crop((467, 54, 770, 462))).getbbox() is None

    decoded = Image.open(gif_path)
    total_duration = 0
    comparison = None
    decoded_frames = []
    for index in range(decoded.n_frames):
        decoded.seek(index)
        decoded.load()
        rgb = decoded.convert("RGB")
        assert rgb.size == (WIDTH, HEIGHT), (index, rgb.size)
        static = rgb.crop((0, 0, WIDTH, 48))
        if comparison is None:
            comparison = static
        else:
            assert ImageChops.difference(comparison, static).getbbox() is None, index
        total_duration += decoded.info.get("duration", 0)
        decoded_frames.append(rgb.copy())
    assert decoded.info.get("loop", 0) == 0
    assert ImageChops.difference(decoded_frames[0], decoded_frames[-1]).getbbox() is None
    assert gif_path.stat().st_size < 6_000_000
    portrait_unique = len({frame.crop((34, 54, 442, 462)).tobytes() for frame in decoded_frames})
    hair_unique = len({frame.crop((134, 74, 424, 224)).tobytes() for frame in decoded_frames})
    text_unique = len({frame.crop((467, 54, 770, 422)).tobytes() for frame in decoded_frames})
    assert portrait_unique > 20 and hair_unique > 20 and text_unique > 40
    assert ImageChops.difference(decoded_frames[0].crop((467, 54, 770, 422)),
                                decoded_frames[-2].crop((467, 54, 770, 422))).getbbox() is None
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
        "profile_text_animated": True,
        "profile_text_unique_frames": text_unique,
        "profile_text_complete_at_loop_end": True,
        "static_fallback_text_complete": True,
        "header_unchanged": True,
        "portrait_animated": True,
        "hair_animated": True,
        "portrait_unique_frames": portrait_unique,
        "hair_unique_frames": hair_unique,
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
