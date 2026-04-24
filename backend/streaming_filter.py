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

    SYSTEM_TAG_PREFIXES = ["[CATAT", "[INGAT", "[STIKER"]
    BLOCK_OPEN  = "[PIKIR]"
    BLOCK_CLOSE = "[/PIKIR]"
    MAX_TAG_BUFFER = 350

    def __init__(self):
        self._buffer = ""
        self._buffering = False
        self._block_suppressing = False   # True = sedang di dalam [PIKIR]...[/PIKIR]
        self._block_buf = ""              # buffer untuk deteksi [/PIKIR]

    def feed(self, chunk: str) -> str:
        output = ""
        for char in chunk:

            # ── Mode block suppress ([PIKIR]...[/PIKIR]) ──
            if self._block_suppressing:
                self._block_buf += char
                # Cek apakah BLOCK_CLOSE sudah lengkap
                if self._block_buf.endswith(self.BLOCK_CLOSE):
                    # Selesai, keluar dari block mode
                    self._block_suppressing = False
                    self._block_buf = ""
                elif len(self._block_buf) > 5000:
                    # Safety: kalau tidak ada penutup, reset
                    self._block_suppressing = False
                    self._block_buf = ""
                continue  # selalu buang karakter dalam block

            # ── Mode buffering (awal `[`) ──
            if self._buffering:
                self._buffer += char

                if char == "]":
                    buf_upper = self._buffer.upper()

                    # Cek apakah ini [PIKIR] opening tag
                    if self._buffer == self.BLOCK_OPEN:
                        self._buffer = ""
                        self._buffering = False
                        self._block_suppressing = True
                        self._block_buf = ""
                    elif any(buf_upper.startswith(p) for p in self.SYSTEM_TAG_PREFIXES):
                        # Single-line system tag → buang
                        self._buffer = ""
                        self._buffering = False
                    else:
                        # Bukan tag sistem → flush sebagai teks biasa
                        output += self._buffer
                        self._buffer = ""
                        self._buffering = False

                elif len(self._buffer) > self.MAX_TAG_BUFFER:
                    # Terlalu panjang → bukan tag, flush
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
        """Panggil di akhir stream untuk mengeluarkan sisa buffer."""
        # Kalau masih block-suppressing, buang saja
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
        if remaining == self.BLOCK_OPEN:
            return ""
        return remaining

    def reset(self):
        """Reset state filter (untuk dipakai ulang di respons berikutnya)."""
        self._buffer = ""
        self._buffering = False
        self._block_suppressing = False
        self._block_buf = ""
