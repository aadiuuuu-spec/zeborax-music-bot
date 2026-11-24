# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import re
import yt_dlp
import random
from difflib import SequenceMatcher
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils


class DummyLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        logger.warning(f"yt-dlp: {msg}")

    def error(self, msg):
        logger.error(f"yt-dlp: {msg}")

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "anony/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )

    def get_cookies(self):
        if not self.checked:
            for file in os.listdir(self.cookie_dir):
                if file.endswith(".txt"):
                    self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        async with aiohttp.ClientSession() as session:
            for url in urls:
                name = url.split("/")[-1]
                link = "https://batbin.me/raw/" + name
                async with session.get(link) as resp:
                    resp.raise_for_status()
                    with open(f"{self.cookie_dir}/{name}.txt", "wb") as fw:
                        fw.write(await resp.read())
        logger.info(f"Cookies saved in {self.cookie_dir}.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except Exception:
            return None
        if results and results["result"]:
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title"),
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )
        return None

    async def search_related(
        self,
        title: str,
        channel: str = "",
        exclude_ids: set[str] | None = None,
        video: bool = False,
        max_duration: int = 3600,
        current_id: str | None = None,
    ) -> Track | None:
        """Find related tracks using YouTube Mix first, then scored search results."""
        excluded = set(exclude_ids or ())

        def title_words(value: str) -> set[str]:
            value = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", value.lower())
            value = re.sub(
                r"\b(official|audio|video|lyrics?|lyrical|remix|cover|version|"
                r"slowed|reverb|sped\s*up|live|4k|hd|visualizer|status|"
                r"karaoke|instrumental|nightcore|loop|reaction)\b",
                " ", value,
            )
            return {
                word for word in re.findall(r"[a-z0-9]+", value)
                if word not in {"the", "a", "an", "song", "from", "movie"}
            }

        def artist_hint(value: str) -> str:
            cleaned = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", value)
            parts = re.split(r"\s(?:-|—|\|)\s", cleaned)
            if len(parts) < 2:
                return ""
            candidate = re.sub(
                r"\b(official|audio|video|lyrics?|lyrical|full song|hd|4k)\b",
                " ", parts[-1], flags=re.IGNORECASE,
            ).strip(" -_|.,")
            if 3 <= len(candidate) <= 45 and len(candidate.split()) <= 5:
                return candidate
            return ""

        original_words = title_words(title)
        clean_title = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", title)
        clean_title = re.sub(
            r"\b(official|audio|video|lyrics?|lyrical|full\s*song)\b",
            " ", clean_title, flags=re.IGNORECASE,
        )
        clean_title = re.sub(r"\s+", " ", clean_title).strip(" -|")
        if not clean_title:
            return None

        artist = artist_hint(title)
        queries = []
        if artist:
            queries.append(f"songs similar to {artist}")
        queries.extend([
            f"songs like {clean_title}",
            f"similar songs to {clean_title}",
            f"{clean_title} radio mix",
        ])

        rejected_versions = re.compile(
            r"\b(cover|karaoke|instrumental|remix|slowed|reverb|sped\s*up|"
            r"nightcore|8d|bass\s*boosted|reaction|lyrics?\s*video|"
            r"live\s*version|looped?)\b",
            re.IGNORECASE,
        )

        source_batches = []
        if current_id:
            try:
                mix_url = f"{self.base}{current_id}&list=RD{current_id}"
                mix = await asyncio.wait_for(Playlist.get(mix_url), timeout=10)
                for rank, data in enumerate((mix or {}).get("videos", [])[:25]):
                    source_batches.append((data, -1, rank, "mix"))
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.debug(f"YouTube Mix lookup unavailable for autoplay: {error}")

        for query_index, query in enumerate(queries):
            try:
                search = VideosSearch(query, limit=10, with_live=False)
                results = await search.next()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.warning(f"Autoplay search failed for query {query!r}: {error}")
                continue
            for rank, data in enumerate((results or {}).get("result", [])):
                source_batches.append((data, query_index, rank, "search"))

        candidates = {}
        normalized_original = " ".join(sorted(original_words))
        for data, query_index, rank, source in source_batches:
            video_id = data.get("id")
            result_title = (data.get("title") or "").strip()
            if not video_id or video_id in excluded or not result_title:
                continue
            if rejected_versions.search(result_title):
                continue

            result_words = title_words(result_title)
            overlap = (
                len(original_words & result_words)
                / max(1, min(len(original_words), len(result_words)))
            )
            normalized_result = " ".join(sorted(result_words))
            title_similarity = SequenceMatcher(
                None, normalized_original, normalized_result
            ).ratio()
            if len(original_words) >= 2 and (
                overlap >= 0.50 or title_similarity >= 0.62
            ):
                continue

            duration = data.get("duration")
            try:
                if isinstance(duration, (int, float)):
                    duration_sec = int(duration)
                else:
                    duration_sec = utils.to_seconds(duration) if duration else 0
            except (TypeError, ValueError):
                continue
            if duration_sec < 90 or duration_sec > max_duration:
                continue

            result_artist = artist_hint(result_title)
            artist_bonus = 0
            if artist and (
                artist.casefold() == result_artist.casefold()
                or artist.casefold() in result_title.casefold()
            ):
                artist_bonus = 18

            if source == "mix":
                score = 100 - rank
            else:
                score = (len(queries) - query_index) * 10 + (10 - rank)
            score += artist_bonus

            thumbnails = data.get("thumbnails") or []
            thumbnail = (
                (thumbnails[-1].get("url") or "").split("?")[0]
                if thumbnails else None
            )
            channel_data = data.get("channel") or {}
            channel_name = (
                channel_data.get("name", "")
                if isinstance(channel_data, dict) else str(channel_data)
            )
            duration_label = str(duration) if duration else (
                f"{duration_sec // 60}:{duration_sec % 60:02d}"
            )
            track = Track(
                id=video_id,
                channel_name=channel_name,
                duration=duration_label,
                duration_sec=duration_sec,
                title=result_title,
                thumbnail=thumbnail,
                url=data.get("link") or f"{self.base}{video_id}",
                video=video,
            )
            old_candidate = candidates.get(video_id)
            if old_candidate is None or score > old_candidate[0]:
                candidates[video_id] = (score, track)

        if not candidates:
            return None

        ranked = sorted(candidates.values(), key=lambda item: item[0], reverse=True)
        return random.choice([track for _, track in ranked[:3]])

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title"),
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        url = self.base + video_id
        ext = "mp4" if video else "webm"
        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists():
            return filename

        cookie = self.get_cookies()
        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "no_warnings": True,
            "overwrites": False,
            "logger": DummyLogger(),
            "nocheckcertificate": True,
            "cookiefile": cookie,
            "remote_components": ["ejs:github"],
        }

        if video:
            ydl_opts = {
                **base_opts,
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio)",
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                **base_opts,
                "format": "bestaudio[ext=webm][acodec=opus]",
            }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as ex:
                    logger.error(f"YouTube download error for {video_id}: {type(ex).__name__}: {ex}")
                    return None
                except Exception as ex:
                    logger.exception(f"Unexpected YouTube download error for {video_id}: {ex}")
                    return None
            return filename

        return await asyncio.to_thread(_download)
