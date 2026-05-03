import re
import logging

# ─────────────────────────────────────────────────────────────
# Pattern-based auto-detection: user introduces themselves
# ─────────────────────────────────────────────────────────────
# Indonesian & English patterns to detect user's name
NAME_PATTERNS = [
    # "nama gw Vathir", "namaku Vathir", "nama saya Vathir"
    r"nama\s*(?:gw|aku|saya|ku|w)\s+(?:adalah\s+|tuh\s+|itu\s+)?([A-Za-z][A-Za-z0-9\s]{1,30}?)(?:[,\.!\?]|$)",
    # "gw Vathir", "w Vathir", "aku Vathir"  
    r"(?:^|[\.\!\?]\s*)(?:gw|w\b|aku|saya)\s+(?:adalah\s+|tuh\s+|nih\s+)?([A-Z][A-Za-z]{2,})",
    # "panggil gw/aku Vathir", "panggil aja Vathir"
    r"panggil\s+(?:gw|aku|saya|w|aja)?\s*([A-Z][A-Za-z]{2,})",
    # "gw Vathir nih", "gw tuh Vathir", "gw ini Vathir"
    r"(?:gw|w\b|aku|saya)\s+(?:tuh|nih|ini|itu)\s+([A-Z][A-Za-z]{2,})",
    # "Vathir nih gw", "Vathir ini gw"
    r"([A-Z][A-Za-z]{2,})\s+(?:nih|ini|itu)\s+(?:gw|w\b|aku|saya)",
    # "perkenalan, gw Vathir" / "hai, gw Vathir"
    r"(?:hai|hi|halo|hey|perkenalan)[,\s]+(?:gw|aku|saya|w)\s+([A-Z][A-Za-z]{2,})",
    # English patterns: "I'm Vathir", "my name is Vathir", "call me Vathir"
    r"(?:i[' ]?m|i am|my name is|call me)\s+([A-Z][A-Za-z]{2,})",
]

# Words that are not names (false positive guard)
NON_NAMES = {
    "ai", "bot", "ga", "gak", "ga", "bisa", "mau", "tau", "lagi", "lagi", "deh",
    "dong", "aja", "sih", "nih", "tuh", "kek", "kan", "ya", "ok", "oke",
    "the", "and", "or", "not", "yes", "no", "it", "is", "are", "was", "were",
    "ada", "tidak", "bukan", "siapa", "apa", "gimana", "kenapa", "kapan", "mana",
    "sangat", "banget", "bgt", "juga", "udah", "sudah", "masih", "belum",
    "baik", "buruk", "senang", "sedih", "marah", "takut", "besar", "kecil",
    "thinking", "thought", "remember", "log", "sticker", "system", "hint",
}

def extract_name_from_user_message(text: str) -> str | None:
    """
    Try to detect if user is introducing their name.
    Returns name if found, None otherwise.
    """
    for pattern in NAME_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            candidate = match.group(1).strip().split()[0]  # Take first word only
            if candidate.lower() not in NON_NAMES and len(candidate) >= 3:
                # Capitalize properly
                return candidate.capitalize()
    return None


# ─────────────────────────────────────────────────────────────
# AI-driven tag parser: [REMEMBER: Name=X, Notes=Y] or [INGAT: ...]
# ─────────────────────────────────────────────────────────────
INGAT_TAG_PATTERN = re.compile(
    r"\[(?:INGAT|REMEMBER):\s*(.*?)\]",
    re.IGNORECASE | re.DOTALL
)

def parse_ingat_tags(ai_response: str) -> list[dict]:
    """
    Parse all [REMEMBER: ...] or [INGAT: ...] tags.
    Returns list of dicts: [{"name": "Vathir", "notes": "..."}, ...]
    """
    results = []
    for match in INGAT_TAG_PATTERN.finditer(ai_response):
        content = match.group(1).strip()
        entry = {}
        # Parse key=value pairs separated by commas
        for part in content.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                key = k.strip().lower()
                val = v.strip()
                if key in ("nama", "name"):
                    entry["name"] = val
                elif key in ("catatan", "notes", "info"):
                    entry["notes"] = val
        if "name" in entry and entry["name"]:
            results.append(entry)
            logging.info(f"[REMEMBER TAG] Parsed: {entry}")
    return results


def strip_ingat_tags(ai_response: str) -> str:
    """Remove [REMEMBER] and [INGAT] tags from output."""
    return INGAT_TAG_PATTERN.sub("", ai_response).strip()


# ─────────────────────────────────────────────────────────────
# LOG tag parser: [LOG: diary entry] or [CATAT: ...]
# ─────────────────────────────────────────────────────────────
CATAT_TAG_PATTERN = re.compile(
    r"\[(?:CATAT|LOG|NOTE)(?:\(([a-zA-Z]+)\))?[:\s]*([^\]]*?)\]",
    re.IGNORECASE
)

def parse_catat_tags(ai_response: str) -> list[dict]:
    """
    Parse all [LOG: ...] or [CATAT: ...] tags.
    Returns list of dicts: [{"category": "eat", "entry": "..."}, ...]
    """
    results = []
    for match in CATAT_TAG_PATTERN.finditer(ai_response):
        category = (match.group(1) or "general").strip().lower()
        entry_text = match.group(2).strip()
        if entry_text:
            results.append({"category": category, "entry": entry_text})
            logging.info(f"[LOG TAG] [{category}] {entry_text[:80]}")
    return results


def strip_catat_tags(ai_response: str) -> str:
    """Remove [LOG] and [CATAT] tags from output."""
    return CATAT_TAG_PATTERN.sub("", ai_response).strip()


def strip_all_system_tags(ai_response: str) -> str:
    """Remove all system tags ([REMEMBER:], [LOG:], [STICKER:], [THINK]...[/THINK])."""
    cleaned = INGAT_TAG_PATTERN.sub("", ai_response)
    cleaned = CATAT_TAG_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\[(?:STIKER|STICKER):[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    # Remove block [THINK] or [PIKIR]
    cleaned = re.sub(r"\[(?:THINK|PIKIR)\].*?\[/(?:THINK|PIKIR)\]", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    return cleaned.strip()


# ─────────────────────────────────────────────────────────────
# STICKER tag parser: [STICKER:filename.webp]
# ─────────────────────────────────────────────────────────────
STIKER_TAG_PATTERN = re.compile(r"\[(?:STIKER|STICKER):([^\]]+)\]", re.IGNORECASE)

def parse_stiker_tag(ai_response: str) -> str | None:
    """
    Find [STICKER:filename] or [STIKER:filename] tag.
    Returns filename if found, None otherwise.
    """
    match = STIKER_TAG_PATTERN.search(ai_response)
    if match:
        return match.group(1).strip()
    return None
