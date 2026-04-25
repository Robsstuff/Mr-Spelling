"""
build_video_pages.py
====================
Pulls all videos from the itsmrspelling YouTube channel and generates
bare-bones HTML lesson pages for the Mr Spelling Netlify website.

Output: Mr Spelling/lessons/[topic-slug].html  +  lessons/index.html

Run from the Mr Spelling folder:
  python build_video_pages.py
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError

# ---------------------------------------------------------------------------
# Unicode-safe console output (Windows cp1252 friendly)
# ---------------------------------------------------------------------------

def safe(s):
    """Return a version of s that prints safely on Windows cp1252 terminals."""
    return s.encode("ascii", errors="replace").decode("ascii")


def sprint(*args, **kwargs):
    """print() with automatic ASCII-safe encoding."""
    safe_args = [safe(str(a)) for a in args]
    print(*safe_args, **kwargs)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
LESSONS_DIR = HERE / "lessons"
LESSONS_DIR.mkdir(exist_ok=True)

# Pull API key from api_keys.py one directory up
sys.path.insert(0, str(HERE.parent))
from api_keys import YOUTUBE_API_KEY, MRSPELLING_CHANNEL_ID

CHANNEL_ID = MRSPELLING_CHANNEL_ID   # UCAk_BNJ7wwnvCiWpbE85d9Q
YT_API_BASE = "https://www.googleapis.com/youtube/v3"


# ---------------------------------------------------------------------------
# Step 1 — Fetch all channel videos via YouTube Data API v3
# ---------------------------------------------------------------------------

def yt_get(endpoint, params):
    params["key"] = YOUTUBE_API_KEY
    url = f"{YT_API_BASE}/{endpoint}?{urlencode(params)}"
    with urlopen(url) as r:
        return json.loads(r.read().decode())


def get_uploads_playlist_id():
    data = yt_get("channels", {"id": CHANNEL_ID, "part": "contentDetails"})
    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_all_videos():
    """Return list of dicts: videoId, title, description, publishedAt, thumbnail."""
    playlist_id = get_uploads_playlist_id()
    sprint(f"Uploads playlist: {playlist_id}")

    videos = []
    page_token = None
    while True:
        params = {
            "playlistId": playlist_id,
            "part": "snippet",
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = yt_get("playlistItems", params)
        for item in data.get("items", []):
            sn = item["snippet"]
            vid = sn["resourceId"]["videoId"]
            thumbs = sn.get("thumbnails", {})
            thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
            videos.append({
                "videoId": vid,
                "title": sn["title"],
                "description": sn["description"],
                "publishedAt": sn["publishedAt"],
                "thumbnail": thumb,
            })
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.1)

    sprint(f"Total videos fetched: {len(videos)}")
    return videos


# ---------------------------------------------------------------------------
# Step 2 — Classify and group videos by topic
# ---------------------------------------------------------------------------

# Title fragments that mark a video as non-spelling (skip it)
OTHER_PATTERNS = [
    r"\bquiz\b",
    r"\bspelling list\b",
    r"\bpe game\b",
    r"\bmultiplication\b",
    r"\bhow many\b",
    r"\bpaper in half\b",
    r"\bcup tower\b",
    r"\bshirt\b",
    r"\bhomophone of the week\b",
    r"\btimer\b",
    r"\bdynamite tips\b",
    r"\bmaths problem\b",
    r"\bdownloadable spelling list\b",
    r"\bspelling list \d+\b",
    r"\bgrade \d+ spelling list\b",
    r"\b1st grade spelling list\b",
    r"\b2nd grade spelling list\b",
    r"\bspot the spelling mistake\b",    # follow-along quiz format
]
OTHER_RE = re.compile("|".join(OTHER_PATTERNS), re.IGNORECASE)

LESSON_PATTERNS = [r"\blesson\b", r"\blearn\b", r"\blearning\b", r"\btutorial\b",
                   r"\bexplained\b", r"\bbreakdown\b"]
LESSON_RE = re.compile("|".join(LESSON_PATTERNS), re.IGNORECASE)

# Words to strip when normalising the topic key
# NOTE: Keep topic-relevant words like "rule", "rules", "phonics", "suffix", "plural"
STOP_WORDS = {
    # Articles/prepositions/conjunctions
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "for",
    "by", "with", "from", "is", "are", "be", "it", "its", "as", "that",
    "this", "these", "those", "not", "all", "can", "will", "do",
    # Mr Spelling branding
    "mr", "spelling", "spells",
    # Format descriptors (not topic identifiers)
    "rap", "song", "lesson", "learn", "learning", "teaching", "teach",
    "tutorial", "official", "lyrics", "music", "video", "educational",
    "education", "grammar", "advanced", "simple", "easy", "quick",
    "practice", "practise", "australian",
    # Common title filler
    "english", "words", "word", "make", "making", "made", "using", "use",
    "how", "what", "why", "when", "type", "common", "version", "loud",
    "catchy", "popular", "swaggy",
}

# Prefix patterns that introduce a topic after a colon/dash
# e.g. "Spelling Rule Rap: <topic>", "Phonics: <topic>"
BOILERPLATE_PREFIX_RE = re.compile(
    r"^(?:"
    r"spelling\s+rules?\s*(?:rap|song|lesson|quiz)?\s*[:/]\s*"
    r"|phonics\s*[:/]\s*"
    r"|the\s+sounds?\s+of\s+"
    r")",
    re.IGNORECASE,
)


def classify(video):
    """Return 'other', 'lesson', or 'song'."""
    t = video["title"]
    if OTHER_RE.search(t):
        return "other"
    if LESSON_RE.search(t):
        return "lesson"
    return "song"


def best_segment(title):
    """
    Extract the most informative short segment from a YouTube title.

    For titles like "Spelling Rule Rap: <topic>" or "Phonics: <topic>",
    returns the <topic> part. Otherwise returns the first segment before
    a pipe | or sentence-ending period.
    """
    t = title.strip()
    # Check for boilerplate prefix ("Spelling Rule: X", "Phonics: X", etc.)
    m = BOILERPLATE_PREFIX_RE.match(t)
    if m:
        rest = t[m.end():]
        # Take first part of the remaining text
        seg = re.split(r"\s*[|.#]\s*", rest)[0].strip()
        if seg:
            return seg
    # Default: first segment before pipe
    seg = re.split(r"\s*\|\s*", t)[0]
    # Then before sentence-ending period (period followed by space or end)
    seg = re.split(r"\.\s+", seg)[0]
    # Then before hashtags
    seg = re.split(r"\s+#", seg)[0]
    return seg.strip()


def topic_key(title):
    """
    Extract a stable, short grouping key from a video title.
    Uses the best_segment first to extract the core topic, then normalises.
    Sorts tokens so "ch tch" == "tch ch".
    """
    seg = best_segment(title)
    t = seg.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    # Allow single-char tokens (important for phonics codes: L, P, QU etc.)
    tokens = [w for w in t.split() if w not in STOP_WORDS]
    key_tokens = sorted(tokens[:3])
    return " ".join(key_tokens).strip()


def display_title_from(title):
    """
    Extract a clean, short display title from a raw video title.
    E.g. "The Floss Rule Rap Song. Learn to double..." -> "The Floss Rule"
    """
    seg = best_segment(title)
    # Strip trailing format words — loop to handle "Rap Song", "Song Lesson" etc.
    FORMAT_TRAIL = re.compile(
        r"\s+(?:rap|song|lesson|quiz|official|version\s*\d*)\s*$",
        re.IGNORECASE,
    )
    for _ in range(4):  # max 4 passes
        new = FORMAT_TRAIL.sub("", seg).strip()
        if new == seg:
            break
        seg = new
    return seg if seg else title[:60]


def title_to_slug(title):
    """Convert a human title to a URL-safe slug."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def group_videos(videos):
    """
    Group songs and lessons by topic.
    Returns list of group dicts:
      { slug, display_title, songs: [...], lessons: [...] }
    sorted alphabetically by display_title.
    """
    groups = {}   # key -> { songs, lessons, titles }

    for v in videos:
        kind = v["type"]
        if kind == "other":
            continue
        key = topic_key(v["title"])
        if not key:
            key = title_to_slug(v["title"])[:30]
        if key not in groups:
            groups[key] = {"songs": [], "lessons": [], "all_titles": []}
        groups[key][kind + "s"].append(v)
        groups[key]["all_titles"].append(v["title"])

    result = []
    for key, g in groups.items():
        all_vids = g["songs"] + g["lessons"]
        if not all_vids:
            continue
        # Choose best display title: prefer song (full title), cleaned up
        primary = (g["songs"] or g["lessons"])[0]
        display = display_title_from(primary["title"])
        if not display:
            display = primary["title"][:60]
        slug = title_to_slug(display)
        result.append({
            "slug": slug,
            "display_title": display,
            "topic_key": key,
            "songs": g["songs"],
            "lessons": g["lessons"],
        })

    result.sort(key=lambda x: x["display_title"].lower())

    # Dedup slugs: if two groups produce the same slug, append -2, -3 etc.
    seen_slugs = {}
    for g in result:
        base = g["slug"]
        if base in seen_slugs:
            seen_slugs[base] += 1
            g["slug"] = f"{base}-{seen_slugs[base]}"
        else:
            seen_slugs[base] = 1

    return result


# ---------------------------------------------------------------------------
# Step 3 — Extract description and PPT link
# ---------------------------------------------------------------------------

DRIVE_RE = re.compile(
    r"https?://(?:docs\.google\.com/(?:presentation|file)/d/|"
    r"drive\.google\.com/(?:file/d/|open\?id=))"
    r"[\w_-]+(?:/[^\s\n<>\"'()]*)?",
    re.IGNORECASE,
)


def extract_description(text):
    """
    Return the first meaningful paragraph from a YouTube description.
    Skips lines that are purely link/resource/download notices.
    """
    # Patterns that indicate a non-content line
    SKIP_LINE_RE = re.compile(
        r"^\s*(?:"
        r"https?://"       # raw URL line
        r"|www\."          # www link
        r"|download\b"     # download notice
        r"|resource\b"     # "Resource Downloads:"
        r"|support\b"      # "Support Mr Spelling:"
        r"|ko-fi"          # Ko-fi link
        r"|patreon"        # Patreon
        r"|subscribe\b"    # subscribe call to action
        r"|follow\b"       # follow on social
        r"|instagram\b"    # social media
        r"|tiktok\b"
        r"|facebook\b"
        r"|twitter\b"
        r"|#\w"            # hashtag line
        r"|🎵|🎶|🎤|📥|👇|👆"   # emoji-only intros
        r")",
        re.IGNORECASE,
    )

    lines = text.splitlines()
    para = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if para:
                break
            continue
        if SKIP_LINE_RE.match(stripped):
            if para:
                break  # stop at first skip-worthy line after content starts
            continue   # skip leading link lines
        para.append(stripped)
        if len(para) >= 6:  # cap at 6 lines
            break

    result = " ".join(para).strip()
    # Remove trailing URL-heavy segments
    result = re.sub(r"\s+https?://\S+.*$", "", result).strip()
    return result if len(result) > 20 else ""


def extract_ppt_link(text):
    """Return the first Google Drive / Docs link found, or None."""
    m = DRIVE_RE.search(text)
    if m:
        return m.group(0).rstrip(".,;)")
    return None


# ---------------------------------------------------------------------------
# Step 4 — Fetch transcript
# ---------------------------------------------------------------------------

# Transcript cache — persists between runs so rate-limited fetches aren't lost
TRANSCRIPT_CACHE_PATH = HERE / "transcript_cache.json"
_transcript_cache = None


def load_transcript_cache():
    global _transcript_cache
    if _transcript_cache is None:
        if TRANSCRIPT_CACHE_PATH.exists():
            _transcript_cache = json.loads(
                TRANSCRIPT_CACHE_PATH.read_text(encoding="utf-8")
            )
        else:
            _transcript_cache = {}
    return _transcript_cache


def save_transcript_cache():
    if _transcript_cache is not None:
        TRANSCRIPT_CACHE_PATH.write_text(
            json.dumps(_transcript_cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def fetch_transcript(video_id):
    """
    Return list of transcript text lines, or [] if unavailable.
    Results are cached in transcript_cache.json to survive re-runs.
    """
    cache = load_transcript_cache()
    if video_id in cache:
        return cache[video_id]  # may be [] (previously failed)

    try:
        from youtube_transcript_api import (
            YouTubeTranscriptApi,
            NoTranscriptFound,
            TranscriptsDisabled,
        )
        api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id, languages=["en"])
            lines = [e.text for e in fetched]
        except NoTranscriptFound:
            try:
                transcript_list = api.list(video_id)
                lines = []
                for t in transcript_list:
                    lines = [e.text for e in t.fetch()]
                    if lines:
                        break
            except Exception:
                lines = []
        except TranscriptsDisabled:
            lines = []
    except Exception as e:
        sprint(f"      Transcript error: {e}")
        lines = None  # None = uncertain (don't cache — may succeed next time)

    if lines is not None:
        cache[video_id] = lines
        save_transcript_cache()

    # Brief pause to avoid hammering YouTube's rate limit
    if lines:
        time.sleep(0.5)  # successful fetch — small pause
    else:
        time.sleep(0.1)  # failed/empty — minimal pause

    return lines or []


def format_transcript_html(lines):
    """Convert transcript lines to HTML. Groups lines into stanzas."""
    if not lines:
        return '<p class="lyrics-placeholder">Lyrics coming soon.</p>'

    cleaned = []
    for line in lines:
        line = re.sub(r"\[.*?\]", "", line).strip()
        # Remove music notation artifacts
        line = re.sub(r"^\s*[*_~`]+\s*", "", line)
        if line:
            cleaned.append(line)

    if not cleaned:
        return '<p class="lyrics-placeholder">Lyrics coming soon.</p>'

    # Group into stanzas using heuristic: new stanza when very short line
    # follows a normal-length line (suggests a section break)
    html_parts = []
    stanza = []
    prev_wc = 0

    for i, line in enumerate(cleaned):
        wc = len(line.split())
        if i > 0 and wc <= 3 and prev_wc > 6:
            if stanza:
                html_parts.append("".join(f"<p>{l}</p>" for l in stanza))
                html_parts.append('<div class="lyric-break"></div>')
                stanza = []
        stanza.append(line)
        prev_wc = wc

    if stanza:
        html_parts.append("".join(f"<p>{l}</p>" for l in stanza))

    return "\n        ".join(html_parts)


# ---------------------------------------------------------------------------
# Step 5 — Generate HTML
# ---------------------------------------------------------------------------

CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Nunito:wght@400;700;900&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #fef08a;
      font-family: 'Nunito', sans-serif;
      color: #1a1a1a;
      min-height: 100vh;
    }

    .page-header {
      background: linear-gradient(135deg, #facc15 0%, #f97316 100%);
      padding: 32px 24px 28px;
      text-align: center;
      border-bottom: 4px solid #1a1a1a;
      position: relative;
    }

    .back-link {
      position: absolute;
      left: 20px;
      top: 50%;
      transform: translateY(-50%);
      font-family: 'Bangers', cursive;
      font-size: 1.1rem;
      letter-spacing: 1px;
      background: #1a1a1a;
      color: #facc15;
      text-decoration: none;
      padding: 6px 16px;
      border-radius: 999px;
    }

    .page-header h1 {
      font-family: 'Bangers', cursive;
      font-size: clamp(2.4rem, 8vw, 4.5rem);
      letter-spacing: 4px;
      color: #1a1a1a;
      text-shadow: 4px 4px 0 #ef4444;
    }

    .cat-nav {
      background: #1a1a1a;
      padding: 14px 20px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: center;
    }

    .cat-nav a {
      font-family: 'Nunito', sans-serif;
      font-weight: 900;
      font-size: 0.8rem;
      background: #333;
      color: #facc15;
      text-decoration: none;
      padding: 4px 12px;
      border-radius: 999px;
      border: 2px solid #facc15;
      transition: background 0.15s;
    }

    .cat-nav a:hover { background: #facc15; color: #1a1a1a; }

    main {
      max-width: 900px;
      margin: 0 auto;
      padding: 40px 20px 60px;
    }

    .content-section { margin-bottom: 52px; }

    .section-heading {
      font-family: 'Bangers', cursive;
      font-size: clamp(1.8rem, 5vw, 2.6rem);
      letter-spacing: 2px;
      color: #ef4444;
      text-shadow: 2px 2px 0 #1a1a1a;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 3px solid #1a1a1a;
    }

    .video-label {
      font-family: 'Bangers', cursive;
      font-size: 1.3rem;
      letter-spacing: 1px;
      color: #1a1a1a;
      margin: 22px 0 10px;
    }

    .video-wrap {
      position: relative;
      padding-bottom: 56.25%;
      height: 0;
      border: 4px solid #1a1a1a;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 6px 6px 0 #1a1a1a;
    }

    .video-wrap iframe {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
    }

    .description-box {
      background: #fff;
      border: 3px solid #1a1a1a;
      border-radius: 12px;
      padding: 24px 28px;
      box-shadow: 5px 5px 0 #1a1a1a;
      font-size: 1.05rem;
      line-height: 1.8;
    }

    .download-btn {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-family: 'Bangers', cursive;
      font-size: 1.2rem;
      letter-spacing: 1px;
      background: #1a1a1a;
      color: #facc15;
      text-decoration: none;
      padding: 12px 28px;
      border-radius: 999px;
      border: 3px solid #1a1a1a;
      box-shadow: 4px 4px 0 #ef4444;
      transition: transform 0.1s, box-shadow 0.1s;
    }

    .download-btn:hover {
      transform: translate(-2px, -2px);
      box-shadow: 6px 6px 0 #ef4444;
    }

    .no-ppt {
      font-weight: 700;
      color: #6b7280;
      font-size: 1rem;
    }

    .lyrics-box {
      background: #fff;
      border: 3px solid #1a1a1a;
      border-radius: 12px;
      padding: 24px 28px;
      box-shadow: 5px 5px 0 #1a1a1a;
      font-size: 1rem;
      line-height: 2;
    }

    .lyrics-box p { margin-bottom: 4px; }

    .lyrics-box .lyric-break {
      margin: 14px 0 10px;
      border-top: 2px dashed #e5e7eb;
    }

    .lyrics-placeholder { color: #9ca3af; font-style: italic; }

    footer {
      background: #facc15;
      text-align: center;
      padding: 20px;
      font-weight: 900;
      font-size: 0.95rem;
      color: #1a1a1a;
      border-top: 4px solid #1a1a1a;
    }
"""

INDEX_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Nunito:wght@400;700;900&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #fef08a;
      font-family: 'Nunito', sans-serif;
      color: #1a1a1a;
      min-height: 100vh;
    }

    .page-header {
      background: linear-gradient(135deg, #facc15 0%, #f97316 100%);
      padding: 32px 24px 28px;
      text-align: center;
      border-bottom: 4px solid #1a1a1a;
      position: relative;
    }

    .back-link {
      position: absolute;
      left: 20px;
      top: 50%;
      transform: translateY(-50%);
      font-family: 'Bangers', cursive;
      font-size: 1.1rem;
      letter-spacing: 1px;
      background: #1a1a1a;
      color: #facc15;
      text-decoration: none;
      padding: 6px 16px;
      border-radius: 999px;
    }

    .page-header h1 {
      font-family: 'Bangers', cursive;
      font-size: clamp(2.4rem, 8vw, 4.5rem);
      letter-spacing: 4px;
      color: #1a1a1a;
      text-shadow: 4px 4px 0 #ef4444;
    }

    .page-header p {
      font-weight: 700;
      font-size: 1.05rem;
      margin-top: 8px;
      opacity: 0.8;
    }

    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 20px 60px;
    }

    .topics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 20px;
    }

    .topic-card {
      background: #fff;
      border: 3px solid #1a1a1a;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 5px 5px 0 #1a1a1a;
      text-decoration: none;
      color: #1a1a1a;
      display: flex;
      flex-direction: column;
      transition: transform 0.1s, box-shadow 0.1s;
    }

    .topic-card:hover {
      transform: translate(-3px, -3px);
      box-shadow: 8px 8px 0 #1a1a1a;
    }

    .topic-card-thumb {
      width: 100%;
      aspect-ratio: 16/9;
      object-fit: cover;
      display: block;
    }

    .topic-card-thumb-placeholder {
      width: 100%;
      aspect-ratio: 16/9;
      background: linear-gradient(135deg, #facc15, #f97316);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Bangers', cursive;
      font-size: 2rem;
      color: #1a1a1a;
      letter-spacing: 2px;
    }

    .topic-card-body {
      padding: 14px 16px 18px;
      flex: 1;
    }

    .topic-card-title {
      font-family: 'Bangers', cursive;
      font-size: 1.35rem;
      letter-spacing: 1px;
      margin-bottom: 8px;
      line-height: 1.2;
    }

    .badge {
      display: inline-block;
      background: #fef08a;
      border: 2px solid #1a1a1a;
      border-radius: 999px;
      padding: 2px 8px;
      margin-right: 4px;
      margin-top: 4px;
      font-size: 0.78rem;
      font-weight: 900;
    }

    footer {
      background: #facc15;
      text-align: center;
      padding: 20px;
      font-weight: 900;
      font-size: 0.95rem;
      color: #1a1a1a;
      border-top: 4px solid #1a1a1a;
    }
"""


def build_video_embeds(songs, lessons):
    parts = []
    total = len(songs) + len(lessons)

    def embed(v, label=None):
        vid = v["videoId"]
        t_attr = v["title"].replace('"', "&quot;")
        label_html = f'<p class="video-label">{label}</p>\n      ' if label else ""
        return (
            f"{label_html}"
            f'<div class="video-wrap">\n'
            f'        <iframe src="https://www.youtube.com/embed/{vid}" '
            f'title="{t_attr}" frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            f'gyroscope; picture-in-picture" allowfullscreen></iframe>\n'
            f"      </div>"
        )

    if total == 1:
        parts.append(embed((songs or lessons)[0]))
    else:
        for v in songs:
            parts.append(embed(v, "Song"))
        for v in lessons:
            parts.append(embed(v, "Lesson"))

    return "\n      ".join(parts)


def build_ppt_block(ppt_url, display_title):
    if ppt_url:
        safe_title = display_title.replace('"', "&quot;")
        return (
            f'<a class="download-btn" href="{ppt_url}" target="_blank" rel="noopener">'
            f"&#128196; Open {safe_title} PowerPoint"
            f"</a>"
        )
    return '<p class="no-ppt">No PowerPoint available for this topic yet.</p>'


def generate_page(group, skip_transcripts=False):
    songs = group["songs"]
    lessons = group["lessons"]
    all_vids = songs + lessons

    # Best description and PPT link
    desc_text = ""
    ppt_url = None
    for v in all_vids:
        if not desc_text:
            d = extract_description(v["description"])
            if d:
                desc_text = d
        if not ppt_url:
            ppt_url = extract_ppt_link(v["description"])

    if not desc_text:
        # Fall back: try ALL videos in the group for any description
        for v in all_vids:
            full_text = v["description"]
            # Try a more lenient extraction — just take first non-empty line
            for line in full_text.splitlines():
                line = line.strip()
                if line and len(line) > 30 and not line.startswith("http"):
                    desc_text = line
                    break
            if desc_text:
                break
    if not desc_text:
        desc_text = f"A spelling rule video by Mr Spelling about {group['display_title']}."

    # Transcript — try song first, then lesson
    transcript_lines = []
    if not skip_transcripts:
        for v in songs + lessons:
            sprint(f"      Fetching transcript: {v['title'][:55]}")
            lines = fetch_transcript(v["videoId"])
            if lines:
                transcript_lines = lines
                sprint(f"      Got {len(lines)} lines")
                break
        if not transcript_lines:
            sprint(f"      No transcript found")

    lyrics_html = format_transcript_html(transcript_lines)
    video_embeds = build_video_embeds(songs, lessons)
    ppt_block = build_ppt_block(ppt_url, group["display_title"])

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mr Spelling &mdash; {group['display_title']}</title>
  <style>{CSS}
  </style>
</head>
<body>

  <header class="page-header">
    <a class="back-link" href="index.html">&#8592; All Topics</a>
    <h1>{group['display_title']}</h1>
  </header>

  <nav class="cat-nav">
    <a href="#video">Video</a>
    <a href="#description">Spelling Rule</a>
    <a href="#powerpoint">PowerPoint</a>
    <a href="#lyrics">Lyrics</a>
  </nav>

  <main>

    <section class="content-section" id="video">
      <h2 class="section-heading">Watch the Video</h2>
      {video_embeds}
    </section>

    <section class="content-section" id="description">
      <h2 class="section-heading">The Spelling Rule</h2>
      <div class="description-box">
        <p>{desc_text}</p>
      </div>
    </section>

    <section class="content-section" id="powerpoint">
      <h2 class="section-heading">PowerPoint</h2>
      {ppt_block}
    </section>

    <section class="content-section" id="lyrics">
      <h2 class="section-heading">Song Lyrics</h2>
      <div class="lyrics-box">
        {lyrics_html}
      </div>
    </section>

  </main>

  <footer>
    &copy; 2025 Mr Spelling &mdash; Not Misspelling
  </footer>

</body>
</html>"""

    out_path = LESSONS_DIR / f"{group['slug']}.html"
    out_path.write_text(page, encoding="utf-8")
    return out_path


def generate_index(groups):
    cards_html = []
    for g in groups:
        all_vids = g["songs"] + g["lessons"]
        thumb = all_vids[0]["thumbnail"] if all_vids else ""
        title = g["display_title"]
        slug = g["slug"]

        badges = []
        if g["songs"]:
            n = len(g["songs"])
            badges.append(f'<span class="badge">{n} song{"s" if n > 1 else ""}</span>')
        if g["lessons"]:
            n = len(g["lessons"])
            badges.append(f'<span class="badge">{n} lesson{"s" if n > 1 else ""}</span>')
        has_ppt = any(extract_ppt_link(v["description"]) for v in all_vids)
        if has_ppt:
            badges.append('<span class="badge">PowerPoint</span>')

        thumb_html = (
            f'<img class="topic-card-thumb" src="{thumb}" alt="{title}" loading="lazy" />'
            if thumb
            else f'<div class="topic-card-thumb-placeholder">{title[:12]}</div>'
        )

        cards_html.append(
            f'      <a class="topic-card" href="{slug}.html">\n'
            f"        {thumb_html}\n"
            f'        <div class="topic-card-body">\n'
            f'          <div class="topic-card-title">{title}</div>\n'
            f"          <div>{''.join(badges)}</div>\n"
            f"        </div>\n"
            f"      </a>"
        )

    cards_block = "\n".join(cards_html)
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mr Spelling &mdash; All Spelling Topics</title>
  <style>{INDEX_CSS}
  </style>
</head>
<body>

  <header class="page-header">
    <a class="back-link" href="../index.html">&#8592; Home</a>
    <h1>All Spelling Topics</h1>
    <p>{len(groups)} topics with videos, lyrics &amp; PowerPoints</p>
  </header>

  <main>
    <div class="topics-grid">
{cards_block}
    </div>
  </main>

  <footer>
    &copy; 2025 Mr Spelling &mdash; Not Misspelling
  </footer>

</body>
</html>"""

    index_path = LESSONS_DIR / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    return index_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(skip_transcripts=False, fresh=False):
    print("=" * 60)
    print("Mr Spelling -- Video Page Builder")
    print("=" * 60)

    # --- Step 1: Fetch ---
    print("\n[1/4] Fetching videos from YouTube channel...")
    raw_path = HERE / "channel_videos_raw.json"
    if raw_path.exists() and not fresh:
        print("  (using cached channel_videos_raw.json)")
        videos = json.loads(raw_path.read_text(encoding="utf-8"))
    else:
        videos = fetch_all_videos()
        raw_path.write_text(json.dumps(videos, indent=2, ensure_ascii=False), encoding="utf-8")
        sprint(f"  Raw data saved to: {raw_path.name}")

    # Classify
    for v in videos:
        v["type"] = classify(v)
    songs_c = sum(1 for v in videos if v["type"] == "song")
    lessons_c = sum(1 for v in videos if v["type"] == "lesson")
    other_c = sum(1 for v in videos if v["type"] == "other")
    print(f"  Songs: {songs_c}  Lessons: {lessons_c}  Other (skipped): {other_c}")

    # --- Step 2: Group ---
    print("\n[2/4] Grouping by topic...")
    groups = group_videos(videos)
    print(f"  Topic groups: {len(groups)}")
    for g in groups:
        s, l = len(g["songs"]), len(g["lessons"])
        sprint(f"    {g['display_title'][:50]:<50} s={s} l={l}")

    # --- Step 3: Generate pages ---
    print(f"\n[3/4] Generating {len(groups)} HTML pages...")
    ppt_count = 0
    transcript_count = 0

    for i, g in enumerate(groups, 1):
        sprint(f"\n  [{i}/{len(groups)}] {g['display_title']}")
        path = generate_page(g, skip_transcripts=skip_transcripts)

        all_vids = g["songs"] + g["lessons"]
        if any(extract_ppt_link(v["description"]) for v in all_vids):
            ppt_count += 1
        content = path.read_text(encoding="utf-8")
        if "lyrics-placeholder" not in content:
            transcript_count += 1

        sprint(f"  Saved: lessons/{path.name}")

    # --- Step 4: Index ---
    print("\n[4/4] Generating lessons/index.html...")
    index_path = generate_index(groups)
    sprint(f"  Index saved: {index_path.name}")

    print("\n" + "=" * 60)
    print("DONE!")
    print(f"  Pages generated   : {len(groups)}")
    print(f"  With PPT links    : {ppt_count}")
    print(f"  With transcripts  : {transcript_count}")
    sprint(f"  Output folder     : {LESSONS_DIR}")
    print("=" * 60)
    print("\nNext step: copy the 'lessons/' folder into your Netlify site and deploy.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mr Spelling video page builder")
    parser.add_argument(
        "--skip-transcripts",
        action="store_true",
        help="Skip transcript fetching (HTML-only regeneration)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Force re-fetch from YouTube (ignore cached channel_videos_raw.json)",
    )
    args = parser.parse_args()
    main(skip_transcripts=args.skip_transcripts, fresh=args.fresh)
