import re
import logging

# ─────────────────────────────────────────────────────────────
# Pattern-based auto-detection: user perkenalkan diri
# ─────────────────────────────────────────────────────────────
# Pattern bahasa Indonesia gaul & formal untuk deteksi nama
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
    # English fallback: "I'm Vathir", "my name is Vathir", "call me Vathir"
    r"(?:i[' ]?m|i am|my name is|call me)\s+([A-Z][A-Za-z]{2,})",
]

# Kata-kata yang bukan nama (false positive guard)
NON_NAMES = {
    "ai", "bot", "ga", "gak", "ga", "bisa", "mau", "tau", "lagi", "lagi", "deh",
    "dong", "aja", "sih", "nih", "tuh", "kek", "kan", "ya", "ok", "oke",
    "the", "and", "or", "not", "yes", "no", "it", "is", "are", "was", "were",
    "ada", "tidak", "bukan", "siapa", "apa", "gimana", "kenapa", "kapan", "mana",
    "sangat", "banget", "bgt", "juga", "udah", "sudah", "masih", "belum",
    "baik", "buruk", "senang", "sedih", "marah", "takut", "besar", "kecil",
}

def extract_name_from_user_message(text: str) -> str | None:
    """
    Coba deteksi apakah user sedang memperkenalkan namanya sendiri.
    Returns nama jika ditemukan, None jika tidak.
    """
    for pattern in NAME_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            candidate = match.group(1).strip().split()[0]  # Ambil kata pertama saja
            if candidate.lower() not in NON_NAMES and len(candidate) >= 3:
                # Capitalize properly
                return candidate.capitalize()
    return None


# ─────────────────────────────────────────────────────────────
# AI-driven tag parser: [INGAT: Nama=X, Catatan=Y]
# ─────────────────────────────────────────────────────────────
# Format yang diajarkan ke AI:
#   [INGAT: Nama=Vathir, Catatan=pemilikku, suka coding]
#   [INGAT: Nama=Budi]
INGAT_TAG_PATTERN = re.compile(
    r"\[INGAT:\s*(.*?)\]",
    re.IGNORECASE | re.DOTALL
)

def parse_ingat_tags(ai_response: str) -> list[dict]:
    """
    Parse semua tag [INGAT: ...] dari response AI.
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
            logging.info(f"[INGAT TAG] Parsed: {entry}")
    return results


def strip_ingat_tags(ai_response: str) -> str:
    """Hapus semua tag [INGAT: ...] dari teks yang akan ditampilkan ke user."""
    return INGAT_TAG_PATTERN.sub("", ai_response).strip()


# ─────────────────────────────────────────────────────────────
# CATAT tag parser: [CATAT: teks catatan harian]
# ─────────────────────────────────────────────────────────────
# AI menulis di buku hariannya sendiri dengan format:
#   [CATAT: tadi ngobrol sama Vathir soal sistem memori, seru banget]
#   [CATAT(makan): barusan makan roti yang dikasih Vathir, enak juga]
#   [CATAT(perasaan): hari ini gw seneng, udah lama ga ngobrol]
CATAT_TAG_PATTERN = re.compile(
    r"\[CATAT(?:\(([a-zA-Z]+)\))?:\s*([^\]]*?)\]",
    re.IGNORECASE
)

def parse_catat_tags(ai_response: str) -> list[dict]:
    """
    Parse semua tag [CATAT: ...] atau [CATAT(kategori): ...] dari response AI.
    Returns list of dicts: [{"category": "makan", "entry": "..."}, ...]
    """
    results = []
    for match in CATAT_TAG_PATTERN.finditer(ai_response):
        category = (match.group(1) or "umum").strip().lower()
        entry_text = match.group(2).strip()
        if entry_text:
            results.append({"category": category, "entry": entry_text})
            logging.info(f"[CATAT TAG] [{category}] {entry_text[:80]}")
    return results


def strip_catat_tags(ai_response: str) -> str:
    """Hapus semua tag [CATAT: ...] dari teks yang akan ditampilkan ke user."""
    return CATAT_TAG_PATTERN.sub("", ai_response).strip()


def strip_all_system_tags(ai_response: str) -> str:
    """Hapus semua tag sistem ([INGAT:], [CATAT:], [STIKER:], [PIKIR]...[/PIKIR]) sekaligus."""
    cleaned = INGAT_TAG_PATTERN.sub("", ai_response)
    cleaned = CATAT_TAG_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\[STIKER:[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    # Hapus blok [PIKIR]...[/PIKIR] (chain-of-thought internal)
    cleaned = re.sub(r"\[PIKIR\].*?\[/PIKIR\]", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    return cleaned.strip()


# ─────────────────────────────────────────────────────────────
# STIKER tag parser: [STIKER:namafile.webp]
# ─────────────────────────────────────────────────────────────
STIKER_TAG_PATTERN = re.compile(r"\[STIKER:([^\]]+)\]", re.IGNORECASE)

def parse_stiker_tag(ai_response: str) -> str | None:
    """
    Cari tag [STIKER:namafile] di response AI.
    Returns nama file stiker jika ada, None jika tidak.
    Hanya ambil stiker pertama yang ditemukan.
    """
    match = STIKER_TAG_PATTERN.search(ai_response)
    if match:
        return match.group(1).strip()
    return None
