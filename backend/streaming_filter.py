class StreamingTagFilter:
    """
    Filter real-time untuk membuang tag sistem dari output streaming sebelum ditampilkan ke user.

    Tag yang dihandle:
    1. Single-line tags  : [CATAT:...], [INGAT:...], [STIKER:...]
    2. Block tags        : [PIKIR]...[/PIKIR]  (chain-of-thought — harus disembunyikan sepenuhnya)

    Cara kerja (single):
    - Setiap karakter `[` memulai buffering
    - Jika `]` ditemukan dan buffer cocok prefix sistem → buang
    - Jika buffer terlalu panjang tanpa `]` → flush sebagai teks normal

    Cara kerja (block [PIKIR]):
    - Saat `[PIKIR]` terdeteksi → aktifkan mode block_suppress
    - Semua karakter dibuang sampai `[/PIKIR]` ditemukan
    """

    SYSTEM_TAG_PREFIXES = ["[CATAT", "[INGAT", "[STIKER", "[LOG", "[REMEMBER", "[STICKER", "[NOTE"]
    BLOCK_OPEN  = "[THINK]"
    BLOCK_CLOSE = "[/THINK]"
    # Legacy support
    LEGACY_BLOCK_OPEN = "[PIKIR]"
    LEGACY_BLOCK_CLOSE = "[/PIKIR]"
    MAX_TAG_BUFFER = 350

    def __init__(self):
        self._buffer = ""
        self._buffering = False
        self._block_suppressing = False   # True = sedang di dalam [PIKIR]...[/PIKIR]
        self._block_buf = ""              # buffer untuk deteksi [/PIKIR]

    def feed(self, chunk: str) -> str:
        output = ""
        for char in chunk:

            # ── Block suppress mode ([THINK]...[/THINK]) ──
            if self._block_suppressing:
                self._block_buf += char
                # Check if BLOCK_CLOSE or LEGACY_BLOCK_CLOSE is complete
                if self._block_buf.endswith(self.BLOCK_CLOSE) or self._block_buf.endswith(self.LEGACY_BLOCK_CLOSE):
                    # Done, exit block mode
                    self._block_suppressing = False
                    self._block_buf = ""
                elif len(self._block_buf) > 5000:
                    # Safety: if no closing tag, reset
                    self._block_suppressing = False
                    self._block_buf = ""
                continue  # always discard chars inside block

            # ── Buffering mode (starts with `[`) ──
            if self._buffering:
                self._buffer += char

                if char == "]":
                    buf_upper = self._buffer.upper()

                    # Check for [THINK] or [PIKIR] opening tag
                    if self._buffer == self.BLOCK_OPEN or self._buffer == self.LEGACY_BLOCK_OPEN:
                        self._buffer = ""
                        self._buffering = False
                        self._block_suppressing = True
                        self._block_buf = ""
                    elif any(buf_upper.startswith(p) for p in self.SYSTEM_TAG_PREFIXES):
                        # Single-line system tag → discard
                        self._buffer = ""
                        self._buffering = False
                    else:
                        # Not a system tag → flush as normal text
                        output += self._buffer
                        self._buffer = ""
                        self._buffering = False

                elif len(self._buffer) > self.MAX_TAG_BUFFER:
                    # Too long → not a tag, flush
                    output += self._buffer
                    self._buffer = ""
                    self._buffering = False

            else:
                if char == "[":
                    self._buffer = "["
                    self._buffering = True
                else:
                    output += char

        return output

    def flush(self) -> str:
        """Call at the end of stream to flush remaining buffer."""
        # If still block-suppressing, just discard
        if self._block_suppressing:
            self._block_suppressing = False
            self._block_buf = ""

        if not self._buffer:
            return ""

        remaining = self._buffer
        self._buffer = ""
        self._buffering = False

        buf_upper = remaining.upper()
        if any(buf_upper.startswith(p) for p in self.SYSTEM_TAG_PREFIXES):
            return ""
        if remaining == self.BLOCK_OPEN or remaining == self.LEGACY_BLOCK_OPEN:
            return ""
        return remaining

    def reset(self):
        """Reset state filter (untuk dipakai ulang di respons berikutnya)."""
        self._buffer = ""
        self._buffering = False
        self._block_suppressing = False
        self._block_buf = ""
