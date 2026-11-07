#!/usr/bin/env python3
"""Render README screenshots, the demo GIF, and the social preview.

The source of truth is session.json, captured from the real program by
capture_session.py. Nothing here invents a screen: every pixel comes from the
recorded ANSI stream.

Install dependencies:
    py -m pip install -r demo-assets/tools/requirements.txt

Run:
    py demo-assets/tools/render_assets.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyte
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = REPO_ROOT / "demo-assets"
TOOLS_DIR = DEMO_DIR / "tools"
SCREENSHOTS_DIR = DEMO_DIR / "screenshots"
SESSION_PATH = TOOLS_DIR / "session.json"

BG = "#0d1117"
TITLE_BG = "#161b22"
BORDER = "#30363d"
MUTED = "#8b949e"
TEXT = "#d6deeb"
ACCENT = "#56d4dd"

PALETTE = {
    "default": TEXT,
    "black": "#484f58",
    "red": "#f85149",
    "green": "#3fb950",
    "brown": "#d29922",
    "blue": "#58a6ff",
    "magenta": "#bc8cff",
    "cyan": "#39c5cf",
    "white": "#b1bac4",
    "brightblack": "#6e7681",
    "brightred": "#ff7b72",
    "brightgreen": "#56d364",
    "brightbrown": "#e3b341",
    "brightblue": "#79c0ff",
    "brightmagenta": "#d2a8ff",
    "brightcyan": "#56d4dd",
    "brightwhite": "#f0f6fc",
}

MONO_REGULAR = [
    r"C:\Windows\Fonts\consola.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    r"C:\Windows\Fonts\cour.ttf",
]
MONO_BOLD = [
    r"C:\Windows\Fonts\consolab.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    r"C:\Windows\Fonts\courbd.ttf",
]
UI_REGULAR = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
UI_BOLD = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def pick_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def load_session(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        session = json.load(handle)
    for key in ("cols", "rows", "chunks", "snapshots"):
        if key not in session:
            raise ValueError(f"{path} is missing {key!r}")
    return session


def screen_at(session: dict, when: float) -> pyte.Screen:
    screen = pyte.Screen(session["cols"], session["rows"])
    stream = pyte.Stream(screen)
    for moment, chunk in session["chunks"]:
        if moment > when:
            break
        stream.feed(chunk)
    return screen


def draw_screen(
    screen: pyte.Screen,
    *,
    cols: int,
    rows: int,
    font_size: int,
    padding: int = 24,
    title_height: int = 38,
    title: str = "Simple ATM Simulation",
    show_cursor: bool = True,
) -> Image.Image:
    regular = pick_font(MONO_REGULAR, font_size)
    bold = pick_font(MONO_BOLD, font_size)
    small = pick_font(UI_REGULAR, 14)
    cell_w = max(1, round(regular.getlength("M")))
    ascent, descent = regular.getmetrics()
    cell_h = max(1, ascent + descent)

    width = padding * 2 + cell_w * cols
    height = title_height + padding * 2 + cell_h * rows
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)

    draw.rectangle([0, 0, width, title_height], fill=TITLE_BG)
    draw.line([0, title_height, width, title_height], fill=BORDER)
    draw.ellipse([16, 14, 26, 24], fill=ACCENT)
    draw.text((36, 11), title, font=small, fill=MUTED)
    draw.rectangle([0, 0, width - 1, height - 1], outline=BORDER)

    ox, oy = padding, title_height + padding
    for y in range(rows):
        row = screen.buffer[y]
        runs: list[tuple[tuple[str, str | None, bool], str]] = []
        current: tuple[tuple[str, str | None, bool], str] | None = None
        for x in range(cols):
            cell = row[x]
            fg = PALETTE.get(cell.fg, TEXT)
            if cell.reverse:
                bg = fg
                fg = BG
            else:
                bg = None
            key = (fg, bg, bool(cell.bold))
            if current is None or current[0] != key:
                if current is not None:
                    runs.append(current)
                current = (key, "")
            current = (current[0], current[1] + cell.data)
        if current is not None:
            runs.append(current)

        x = ox
        for (fg, bg, is_bold), text in runs:
            if not text:
                continue
            run_width = len(text) * cell_w
            if bg is not None:
                draw.rectangle(
                    [x, oy + y * cell_h, x + run_width, oy + (y + 1) * cell_h],
                    fill=bg,
                )
            draw.text(
                (x, oy + y * cell_h),
                text,
                font=bold if is_bold else regular,
                fill=fg,
            )
            x += run_width

    if (
        show_cursor
        and not screen.cursor.hidden
        and screen.cursor.y < rows
        and screen.cursor.x < cols
    ):
        cx = ox + screen.cursor.x * cell_w
        cy = oy + screen.cursor.y * cell_h
        draw.rectangle([cx, cy + 2, cx + cell_w - 1, cy + cell_h - 2], fill=ACCENT)

    return image


def render_screenshots(session: dict) -> list[Path]:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        ("main_menu", "01-main-menu.png"),
        ("sign_in", "02-sign-in.png"),
        ("dashboard", "03-dashboard.png"),
        ("history", "04-history.png"),
    ]
    written: list[Path] = []
    for snapshot, filename in targets:
        if snapshot not in session["snapshots"]:
            raise ValueError(f"snapshot missing from session: {snapshot}")
        moment = max(0.0, session["snapshots"][snapshot] - 0.02)
        screen = screen_at(session, moment)
        image = draw_screen(screen, cols=74, rows=24, font_size=20)
        path = SCREENSHOTS_DIR / filename
        image.save(path, optimize=True)
        written.append(path)
    return written


def render_gif(session: dict) -> tuple[Path, int]:
    """Animate the real loading screen, then hold complete captured screens.

    The interactive screens are taken from the deliberate pauses in
    capture_session.py, so the GIF never shows a half-drawn box or a stray
    mid-render cursor.
    """
    splash_end = session["snapshots"].get("splash", 1.5)
    frames: list[Image.Image] = []
    durations: list[int] = []

    screen = pyte.Screen(session["cols"], session["rows"])
    stream = pyte.Stream(screen)
    chunk_index = 0
    previous: bytes | None = None
    moment = 0.0
    while moment <= splash_end:
        while (
            chunk_index < len(session["chunks"])
            and session["chunks"][chunk_index][0] <= moment
        ):
            stream.feed(session["chunks"][chunk_index][1])
            chunk_index += 1
        image = draw_screen(
            screen,
            cols=74,
            rows=24,
            font_size=16,
            padding=16,
            title_height=30,
        )
        raw = image.tobytes()
        is_blank = not any(
            cell.data.strip() for row in screen.buffer.values() for cell in row.values()
        )
        if raw != previous and (frames or not is_blank):
            frames.append(image)
            durations.append(100)
            previous = raw
        moment += 0.1

    keyframes = [
        ("main_menu", 1100),
        ("sign_in", 1100),
        ("welcome", 1000),
        ("dashboard", 1100),
        ("deposit_result", 1100),
        ("history", 1200),
        ("goodbye", 1100),
    ]
    for snapshot, duration in keyframes:
        if snapshot not in session["snapshots"]:
            continue
        image = draw_screen(
            screen_at(session, max(0.0, session["snapshots"][snapshot] - 0.02)),
            cols=74,
            rows=24,
            font_size=16,
            padding=16,
            title_height=30,
            show_cursor=snapshot not in {"welcome", "goodbye"},
        )
        frames.append(image)
        durations.append(duration)

    if not frames:
        raise ValueError("no frames captured")

    unique_frames: list[Image.Image] = []
    unique_durations: list[int] = []
    previous = None
    for frame, duration in zip(frames, durations):
        raw = frame.tobytes()
        if raw == previous:
            unique_durations[-1] += duration
        else:
            unique_frames.append(frame)
            unique_durations.append(duration)
            previous = raw

    palette_frames = [
        frame.convert("P", palette=Image.ADAPTIVE, colors=64)
        for frame in unique_frames
    ]
    path = DEMO_DIR / "demo.gif"
    palette_frames[0].save(
        path,
        save_all=True,
        append_images=palette_frames[1:],
        duration=unique_durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return path, len(palette_frames)


def render_social_preview() -> Path:
    canvas = Image.new("RGB", (1280, 640), BG)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 8, 640], fill=ACCENT)

    title_font = pick_font(UI_BOLD, 54)
    subtitle_font = pick_font(UI_REGULAR, 26)
    body_font = pick_font(UI_REGULAR, 20)
    small_font = pick_font(UI_REGULAR, 18)

    draw.text((72, 92), "Simple ATM", font=title_font, fill=TEXT)
    draw.text((72, 154), "Simulation", font=title_font, fill=ACCENT)
    draw.text((72, 238), "C++17 console banking simulator", font=subtitle_font, fill="#c9d1d9")
    draw.text((72, 296), "PIN authentication · multi-account banking", font=body_font, fill=MUTED)
    draw.text((72, 330), "Deposits · withdrawals · transaction history", font=body_font, fill=MUTED)

    pill_text = "Single file · No dependencies"
    pill_font = pick_font(UI_BOLD, 18)
    pill_bbox = draw.textbbox((0, 0), pill_text, font=pill_font)
    pill_w = pill_bbox[2] + 36
    pill_h = 42
    draw.rounded_rectangle([72, 396, 72 + pill_w, 396 + pill_h], radius=21, outline=ACCENT, width=2)
    draw.text((90, 406), pill_text, font=pill_font, fill=ACCENT)

    draw.text(
        (72, 566),
        "github.com/ShahabAhmed01/Simple-ATM-Simulation",
        font=small_font,
        fill=MUTED,
    )

    screenshot_path = SCREENSHOTS_DIR / "03-dashboard.png"
    if not screenshot_path.is_file():
        raise FileNotFoundError(f"missing screenshot: {screenshot_path}")
    shot = Image.open(screenshot_path).convert("RGB")
    target_h = 430
    target_w = round(shot.width * target_h / shot.height)
    shot = shot.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = 1280 - target_w - 72
    y = 105
    shadow = Image.new("RGBA", (target_w + 24, target_h + 24), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [8, 8, target_w + 16, target_h + 16], radius=12, fill=(0, 0, 0, 120)
    )
    canvas.paste(shadow, (x - 8, y - 4), shadow)
    canvas.paste(shot, (x, y))
    draw.rounded_rectangle(
        [x, y, x + target_w, y + target_h], radius=4, outline=BORDER, width=1
    )

    path = DEMO_DIR / "social-preview.png"
    canvas.save(path, optimize=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, default=SESSION_PATH)
    args = parser.parse_args()

    session = load_session(args.session)
    screenshots = render_screenshots(session)
    for path in screenshots:
        print(f"wrote {path} ({path.stat().st_size // 1024} KB)")

    gif_path, frame_count = render_gif(session)
    print(f"wrote {gif_path} ({frame_count} frames, {gif_path.stat().st_size // 1024} KB)")

    preview = render_social_preview()
    print(f"wrote {preview} ({preview.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
