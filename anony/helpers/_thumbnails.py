# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# ZeboraX dynamic YouTube music-player artwork.

import os
import random

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from anony import config
from anony.helpers import Track


SIZE = (1280, 720)
ACCENTS = [
    (255, 55, 95), (255, 55, 190), (180, 75, 255),
    (55, 115, 255), (35, 210, 255), (35, 225, 155),
    (255, 195, 55), (255, 120, 45), (255, 80, 145),
    (100, 75, 255), (40, 240, 190), (255, 155, 45),
]


def _font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _fit(text: str, font, max_width: int) -> str:
    text = str(text or "Unknown")
    if font.getlength(text) <= max_width:
        return text
    while len(text) > 4 and font.getlength(text + "…") > max_width:
        text = text[:-1]
    return text.rstrip() + "…"


def _seconds(value: str) -> int:
    try:
        parts = [int(part) for part in str(value).split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except (TypeError, ValueError):
        pass
    return 0


def _views(value) -> str:
    raw = str(value or "0").replace(",", "").strip()
    if any(mark in raw.lower() for mark in ("k", "m", "b")):
        return raw if "view" in raw.lower() else f"{raw} views"
    try:
        number = int("".join(ch for ch in raw if ch.isdigit()))
        if number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M views"
        if number >= 1_000:
            return f"{number / 1_000:.1f}K views"
        return f"{number} views"
    except ValueError:
        return raw or "YouTube"


def _fallback_art(size, accent):
    base = Image.new("RGB", size, (15, 18, 38))
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for index in range(12):
        radius = 35 + index * 13
        x = size[0] // 2 + (index % 4 - 2) * 65
        y = size[1] // 2 + (index // 4 - 1) * 65
        draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                     fill=(*accent, max(8, 34-index*2)))
    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(base)
    font = _font("anony/helpers/Raleway-Bold.ttf", 150)
    draw.text((size[0] // 2 - 55, size[1] // 2 - 95), "♪",
              font=font, fill=(245, 250, 255))
    return base


class Thumbnail:
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.title_font = _font("anony/helpers/Raleway-Bold.ttf", 59)
        self.meta_font = _font("anony/helpers/Inter-Light.ttf", 35)
        self.views_font = _font("anony/helpers/Inter-Light.ttf", 31)
        self.time_font = _font("anony/helpers/Raleway-Bold.ttf", 28)
        self.brand_font = _font("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 25)

    async def start(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def _download_art(self, url: str, path: str) -> bool:
        if not url or not self.session or self.session.closed:
            return False
        try:
            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=12)
            ) as response:
                response.raise_for_status()
                data = await response.read()
            if len(data) < 1500:
                return False
            with open(path, "wb") as output:
                output.write(data)
            return True
        except (aiohttp.ClientError, OSError, ValueError):
            return False

    async def generate(self, song: Track, size=SIZE) -> str:
        try:
            os.makedirs("cache", exist_ok=True)
            output = f"cache/{song.id}_zeborax_thumb_v2.png"
            if os.path.exists(output):
                return output

            accent = random.choice(ACCENTS)
            raw_path = f"cache/{song.id}_art.jpg"
            downloaded = await self._download_art(song.thumbnail, raw_path)

            if downloaded:
                try:
                    artwork = Image.open(raw_path).convert("RGB")
                except (OSError, ValueError):
                    artwork = _fallback_art((480, 480), accent)
            else:
                artwork = _fallback_art((480, 480), accent)

            width, height = size
            background = ImageOps.fit(
                artwork, (width + 160, height + 160),
                method=Image.Resampling.LANCZOS
            ).crop((80, 80, width + 80, height + 80))
            background = background.filter(ImageFilter.GaussianBlur(42))
            background = ImageEnhance.Brightness(background).enhance(0.42)
            canvas = background.convert("RGBA")
            canvas.alpha_composite(
                Image.new("RGBA", size, (8, 10, 19, 145))
            )

            draw = ImageDraw.Draw(canvas)
            draw.rectangle((0, 0, width - 1, height - 1),
                           outline=(*accent, 255), width=12)

            # Album artwork with a soft coloured halo.
            card_x, card_y, card_size = 58, 125, 470
            glow = Image.new("RGBA", size, (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            for spread in range(65, 5, -8):
                gd.rounded_rectangle(
                    (card_x-spread, card_y-spread,
                     card_x+card_size+spread, card_y+card_size+spread),
                    radius=58, outline=(*accent, max(8, 95-spread)),
                    width=12
                )
            canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(24)))

            art = ImageOps.fit(
                artwork, (card_size, card_size),
                method=Image.Resampling.LANCZOS
            ).convert("RGBA")
            mask = Image.new("L", art.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, card_size-1, card_size-1), radius=38, fill=255
            )
            canvas.paste(art, (card_x, card_y), mask)
            draw = ImageDraw.Draw(canvas)
            draw.rounded_rectangle(
                (card_x, card_y, card_x+card_size, card_y+card_size),
                radius=38, outline=(*accent, 255), width=7
            )

            text_x = 600
            text_width = width - text_x - 55
            draw.text((text_x, 75), "˹ᴢᴇʙᴏʀᴧ ꭙ мᴜsɪᴄ˼ ♪",
                      font=self.brand_font, fill=(*accent, 255))
            draw.ellipse((1080, 83, 1097, 100), fill=(*accent, 255))
            draw.text((1110, 76), "PLAYING", font=self.views_font,
                      fill=(235, 240, 250, 255))

            title = _fit(song.title or "Unknown Track",
                         self.title_font, text_width)
            artist = _fit(song.channel_name or "YouTube",
                          self.meta_font, text_width)
            draw.text((text_x, 205), "NOW PLAYING",
                      font=self.views_font, fill=(*accent, 255))
            draw.text((text_x-3, 270), title,
                      font=self.title_font, fill=(255, 255, 255, 255))
            draw.text((text_x, 355), f"Artist: {artist}",
                      font=self.meta_font, fill=(215, 220, 230, 255))
            draw.text((text_x, 410), _views(song.view_count),
                      font=self.views_font, fill=(165, 175, 190, 255))

            # Equalizer motif.
            heights = [25, 48, 35, 72, 42, 86, 31, 62, 40, 75, 28, 55]
            bar_x = text_x
            for bar_height in heights:
                draw.rounded_rectangle(
                    (bar_x, 500-bar_height//2, bar_x+12, 500+bar_height//2),
                    radius=6, fill=(*accent, 235)
                )
                bar_x += 24

            # Playback line: starts at a visible 70% preview, matching the
            # reference artwork; this is decorative, not a live seek position.
            bar_left, bar_top, bar_width, bar_height = text_x, 575, text_width, 10
            draw.rounded_rectangle(
                (bar_left, bar_top, bar_left+bar_width, bar_top+bar_height),
                radius=6, fill=(90, 95, 110, 220)
            )
            filled = int(bar_width * 0.70)
            draw.rounded_rectangle(
                (bar_left, bar_top, bar_left+filled, bar_top+bar_height),
                radius=6, fill=(*accent, 255)
            )
            draw.ellipse(
                (bar_left+filled-8, bar_top-5, bar_left+filled+8, bar_top+15),
                fill=(255, 255, 255, 255)
            )
            draw.text((bar_left, 610), "NOW",
                      font=self.time_font, fill=(195, 205, 218, 255))
            duration = str(song.duration or "LIVE")
            duration_width = self.time_font.getlength(duration)
            draw.text((bar_left+bar_width-duration_width, 610), duration,
                      font=self.time_font, fill=(195, 205, 218, 255))
            draw.text((58, 635), "♪  MUSIC FOR YOUR MOMENT",
                      font=self.views_font, fill=(195, 205, 218, 255))

            canvas.convert("RGB").save(output, "PNG", optimize=True)
            if os.path.exists(raw_path):
                os.remove(raw_path)
            return output
        except Exception:
            return config.DEFAULT_THUMB
