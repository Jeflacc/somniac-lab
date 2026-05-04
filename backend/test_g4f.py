import asyncio
from g4f.client import AsyncClient

async def main():
    try:
        client = AsyncClient()
        response = await client.chat.completions.create(
            model="llama-3.1-70b",
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
