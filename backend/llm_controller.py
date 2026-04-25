import os
import aiohttp
import logging
import json
import time

class LLMController:
    def __init__(
        self,
        provider: str = "ollama",
        api_key: str = "",
        model_name: str = "",
        host: str = "http://127.0.0.1:11434",
        api_keys: list[str] = None,   # Multiple Groq keys for rotation
    ):
        self.provider = provider.lower()
        self.model_name = model_name
        self.host = host

        # ── Key pool: supports multiple Groq keys ──
        if api_keys:
            self._key_pool = [k for k in api_keys if k]
        elif api_key:
            self._key_pool = [api_key]
        else:
            self._key_pool = []

        # Index of currently active key
        self._key_index = 0
        # Tracks keys exhausted for the day: key → unix timestamp when 429 hit
        self._key_exhausted: dict[str, float] = {}

        if self.provider == "groq":
            self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        else:
            self.endpoint = f"{self.host}/api/chat"

        self._session = None

    # ── Active key helpers ──

    @property
    def api_key(self) -> str:
        """Return the current active key."""
        if not self._key_pool:
            return ""
        return self._key_pool[self._key_index % len(self._key_pool)]

    def _mark_key_exhausted(self):
        """Mark current key as daily-limit exhausted and rotate to next."""
        key = self.api_key
        self._key_exhausted[key] = time.time()
        logging.warning(f"[LLM] Key ...{key[-8:]} harian habis. Mencoba key berikutnya.")

        # Try the next available key
        for _ in range(len(self._key_pool)):
            self._key_index = (self._key_index + 1) % len(self._key_pool)
            candidate = self._key_pool[self._key_index]
            # Consider a key "refreshed" if 24h have passed (86400s)
            exhausted_at = self._key_exhausted.get(candidate, 0)
            if time.time() - exhausted_at > 86400:
                logging.info(f"[LLM] Beralih ke key ...{candidate[-8:]}")
                return True
        logging.error("[LLM] SEMUA key Groq sudah habis limit hariannya!")
        return False

    # ── Session ──

    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Main generation ──

    async def generate_response_stream(
        self,
        static_system_prompt: str,
        user_prompt: str = None,
        chat_history: list = None,
    ):
        """
        Berkomunikasi dengan API pilihan (Ollama/Groq) secara streaming.
        Untuk Groq: otomatis ganti key saat 429 daily limit.
        """
        # 1. Static system prompt
        messages = [{"role": "system", "content": static_system_prompt}]
        # 2. Chat history
        if chat_history:
            messages.extend(chat_history)
        # 3. User message
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
        }

        if self.provider == "ollama":
            payload["keep_alive"] = "1h"

        if self.provider == "groq":
            payload["max_tokens"] = 900  # Sedikit lebih hemat — 900 token output per request

        # For Groq: retry with next key on 429, max len(key_pool) attempts
        max_attempts = len(self._key_pool) if self.provider == "groq" else 1
        for attempt in range(max_attempts):
            result = await self._try_request(payload)
            if result == "RATE_LIMIT_DAILY":
                rotated = self._mark_key_exhausted()
                if not rotated:
                    yield "*Sigh* ... (All Groq API keys reached daily limit, try again tomorrow 😞)"
                    return
                # Retry loop with new key
                continue
            else:
                # Yield all content from result generator
                async for chunk in result:
                    yield chunk
                return

        yield "*Sigh* ... (All Groq API keys reached daily limit 😞)"

    async def _try_request(self, payload: dict):
        """
        Execute one HTTP request.
        Returns an async generator of text chunks,
        OR the string "RATE_LIMIT_DAILY" if 429 daily limit hit.
        """
        headers = {}
        if self.provider == "groq":
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

        try:
            session = await self.get_session()
            resp = await session.post(self.endpoint, headers=headers, json=payload)

            if resp.status == 429:
                err_text = await resp.text()
                logging.warning(f"[LLM] 429 from Groq key ...{self.api_key[-8:]}: {err_text[:120]}")
                # Check if it's daily exhaustion (not per-minute)
                is_daily = "day" in err_text.lower() or "daily" in err_text.lower() or "rate_limit_exceeded" in err_text.lower()
                if is_daily:
                    return "RATE_LIMIT_DAILY"
                else:
                    # Per-minute limit — short wait then return error
                    logging.warning("[LLM] Per-minute limit (10k TPM). Waiting 15 seconds.")
                    import asyncio
                    await asyncio.sleep(15)
                    return "RATE_LIMIT_DAILY"  # Let caller retry with same or rotated key

            if resp.status != 200:
                err_text = await resp.text()
                logging.error(f"{self.provider.capitalize()} API Error {resp.status}: {err_text}")
                return self._error_gen(f"Error {self.provider.capitalize()} [{resp.status}]: {err_text[:80]}")

            return self._stream_response(resp)

        except Exception as e:
            logging.error(f"Error LLM Controller: {e}")
            return self._error_gen(f"Connection lost or {self.provider.capitalize()} server is down.")

    async def _stream_response(self, resp):
        """Parse streaming response dari Groq (OpenAI SSE) atau Ollama (JSON lines)."""
        async for line in resp.content:
            if not line:
                continue
            line_str = line.decode("utf-8").strip()

            if self.provider == "groq":
                if line_str.startswith("data: "):
                    if line_str == "data: [DONE]":
                        break
                    try:
                        data = json.loads(line_str[6:])
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
            else:
                try:
                    data = json.loads(line_str)
                    if "error" in data:
                        err = data["error"]
                        logging.error(f"Ollama Internal Stream Error: {err}")
                        yield f"\n[System Error: {err}]"
                        break
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        if content:
                            yield content
                    if data.get("done") and "message" not in data:
                        logging.error(f"Ollama Done WITHOUT message: {line_str}")
                except json.JSONDecodeError:
                    logging.error(f"Ollama Decode Error: {line_str}")
                    continue

    async def _error_gen(self, msg: str):
        """Yield a single error message as async generator."""
        yield f"*Sigh* ... ({msg})"
