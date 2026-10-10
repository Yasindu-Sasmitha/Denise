"""Voice-triggered browser actions for Denise.

    parse_command(text) -> action dict, or None   (pure: no network, no browser)
    plan(action)        -> (what to say, url)     (may look up a YouTube video)
    open_url(url)       -> True / False           (opens the default browser)

Supported phrases (a polite lead-in like "hey Denise, can you ..." is ignored):
    "play despacito on YouTube" / "play lofi beats"      -> finds a video and opens it
    "search YouTube for guitar lessons"                  -> opens YouTube results
    "search for python tutorials" / "google how to ..."  -> opens a Google search
    "open YouTube" / "open Google" / "open the browser"  -> opens that site

URLs are only ever built from the fixed templates below with the query URL-encoded,
so nothing a speech recogniser mishears can make her open an arbitrary address.
"""
import html
import os
import re
import webbrowser
from urllib.parse import quote_plus

import requests

SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "browser": "https://www.google.com",
    "chrome": "https://www.google.com",
}
SITE_NAMES = {"youtube": "YouTube", "google": "Google", "gmail": "Gmail",
              "github": "GitHub", "browser": "the browser", "chrome": "the browser"}

GOOGLE_SEARCH = "https://www.google.com/search?q="
YT_RESULTS = "https://www.youtube.com/results?search_query="
YT_WATCH = "https://www.youtube.com/watch?v="
YT_API = "https://www.googleapis.com/youtube/v3/search"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

# ---------------------------------------------------------------- parsing

_LEAD = re.compile(
    r"^(?:(?:hey|ok|okay)[, ]+)?(?:denise[, ]+)?"
    r"(?:(?:(?:can|could|would|will) you|please|i want you to|i want to|i wanna|let'?s|go and)[, ]+)*"
)
_TRAIL = re.compile(r"(?:[, ]+(?:please|for me|thanks|thank you))+$")

_YT_SEARCH_A = re.compile(r"^(?:search|find|look up|look for) (?:on )?youtube (?:for )?(.+)$")
_YT_SEARCH_B = re.compile(r"^(?:search|find|look up|look for) (?:for )?(.+?) (?:on|in|at) youtube$")
_YT_PLAY_ON = re.compile(r"^(?:play|watch|put on|stream) (.+?) (?:on|in|from|using) youtube$")
_YT_OPEN_AND = re.compile(r"^(?:open |go to )?youtube(?: and| then)? (play|watch|search(?: for)?) (.+)$")
_BARE_PLAY = re.compile(r"^play (?:me )?(?:some )?(.+)$")
_OPEN_SITE = re.compile(r"^open(?: up)? (?:the )?(youtube|google|gmail|github|browser|chrome)$")
_WEB_SEARCH = re.compile(
    r"^(?:search|look up|google(?! (?:is|was|has|are|and|does|did)\b)) "
    r"(?:google |the web |the internet |online )?(?:for )?(.+?)"
    r"(?: (?:on|in|using) (?:google|the web|the internet|the browser|chrome))?$"
)

# things people say to a robot that start with "play" but are just chat
_CHAT_PLAY = re.compile(r"^(?:a\s+)?(?:games?|round)\b|^with\s+(?:me|us|you)\b|^(?:around|along|dead)$")
_VAGUE = re.compile(r"^(?:it|that|this|something|anything|one)$")
_NOT_A_WEB_QUERY = re.compile(r"^(?:your|my)\b")  # "search your memory" is not a web search


def _normalise(text):
    t = text.lower().replace("’", "'").strip()
    t = re.sub(r"[.!?]+$", "", t).strip()
    t = _LEAD.sub("", t, count=1)
    t = _TRAIL.sub("", t)
    return t.strip()


def _make(kind, query):
    q = re.sub(r"^(?:some|me)\s+", "", query.strip())
    if not q or _VAGUE.match(q):
        return None
    if kind == "youtube_play" and q == "youtube":
        return {"kind": "open", "site": "youtube"}
    return {"kind": kind, "query": q}


def parse_command(text):
    """Return an action dict for browser commands, or None for ordinary conversation."""
    t = _normalise(text)
    if not t:
        return None

    m = _OPEN_SITE.match(t)
    if m:
        return {"kind": "open", "site": m.group(1)}

    m = _YT_OPEN_AND.match(t)
    if m:
        kind = "youtube_search" if m.group(1).startswith("search") else "youtube_play"
        return _make(kind, m.group(2))

    for pattern in (_YT_SEARCH_A, _YT_SEARCH_B):
        m = pattern.match(t)
        if m:
            return _make("youtube_search", m.group(1))

    m = _YT_PLAY_ON.match(t)
    if m:
        return _make("youtube_play", m.group(1))

    m = _BARE_PLAY.match(t)
    if m and not _CHAT_PLAY.match(m.group(1)):
        return _make("youtube_play", m.group(1))

    m = _WEB_SEARCH.match(t)
    if m and not _NOT_A_WEB_QUERY.match(m.group(1)):
        return _make("web_search", m.group(1))

    return None

# ---------------------------------------------------------------- YouTube lookup


def _redact(err, secret):
    msg = str(err)
    return msg.replace(secret, "***") if secret else msg


def find_youtube_video(query):
    """Return (video_id, title) for the top YouTube result, or None.

    1) YouTube Data API v3 if YOUTUBE_API_KEY is set (the official, reliable route)
    2) yt-dlp if it is installed (no key needed)
    Returns None if neither works; the caller then falls back to the results page.
    """
    key = os.getenv("YOUTUBE_API_KEY")
    if key:
        try:
            r = requests.get(
                YT_API,
                params={"part": "snippet", "q": query, "type": "video", "maxResults": 1, "key": key},
                timeout=8,
            )
            r.raise_for_status()
            items = r.json().get("items") or []
            if items:
                vid = items[0]["id"]["videoId"]
                if VIDEO_ID.match(vid):
                    return vid, html.unescape(items[0]["snippet"]["title"])
        except Exception as e:  # never print the key: requests puts the full URL in its errors
            print(f"YouTube API error: {_redact(e, key)}")

    try:
        import yt_dlp
    except ImportError:
        return None
    try:
        opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist",
                "skip_download": True, "socket_timeout": 8}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        entries = (info or {}).get("entries") or []
        if entries and entries[0] and VIDEO_ID.match(entries[0].get("id") or ""):
            return entries[0]["id"], entries[0].get("title") or query
    except Exception as e:
        print(f"yt-dlp error: {e}")
    return None

# ---------------------------------------------------------------- doing it


def _short(title, limit=60):
    title = re.sub(r"\s+", " ", title).strip()
    return title if len(title) <= limit else title[:limit].rsplit(" ", 1)[0] + "..."


def plan(action):
    """Work out what Denise should say and which URL to open. Does not open anything."""
    kind = action["kind"]
    if kind == "open":
        site = action["site"]
        return f"Opening {SITE_NAMES[site]}!", SITES[site]

    q = action["query"]
    if kind == "web_search":
        return f"Okay! Searching the web for {q}.", GOOGLE_SEARCH + quote_plus(q)
    if kind == "youtube_search":
        return f"Searching YouTube for {q}.", YT_RESULTS + quote_plus(q)

    # youtube_play
    video = find_youtube_video(q)
    if video:
        vid, title = video
        return f"Playing {_short(title)} on YouTube.", YT_WATCH + vid
    return (f"I couldn't pick a video myself, so here are the YouTube results for {q}.",
            YT_RESULTS + quote_plus(q))


def open_url(url):
    try:
        return bool(webbrowser.open(url, new=2))
    except Exception as e:
        print(f"Browser error: {e}")
        return False
