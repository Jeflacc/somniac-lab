import asyncio
import discord
import logging
import os
from cryptography.fernet import Fernet

# Fetch encryption key from env
_fernet = None
def get_fernet():
    global _fernet
    if _fernet is None:
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY is not set in environment variables.")
        _fernet = Fernet(key.encode())
    return _fernet

def encrypt_token(token: str) -> str:
    f = get_fernet()
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    f = get_fernet()
    return f.decrypt(encrypted_token.encode()).decode()

active_discord_bots = {}  # agent_id: {"client": discord.Client, "task": asyncio.Task}

class SomniacDiscordBot(discord.Client):
    def __init__(self, agent_id: int, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, **kwargs)
        self.agent_id = agent_id

    async def on_ready(self):
        logging.info(f"[DISCORD] Agent {self.agent_id} logged in as {self.user}")

    async def on_message(self, message):
        # Ignore own messages
        if message.author == self.user:
            return
            
        # We can route this to the Somniac engine in the future if we want her to reply instantly to DMs.
        pass

async def start_discord_bot(agent_id: int, token: str):
    """Start a discord bot for a specific agent if not already running."""
    if agent_id in active_discord_bots:
        logging.info(f"[DISCORD] Agent {agent_id} already has an active discord bot.")
        return
        
    client = SomniacDiscordBot(agent_id=agent_id)
    
    async def run_bot():
        try:
            await client.start(token)
        except Exception as e:
            logging.error(f"[DISCORD] Agent {agent_id} bot failed: {e}")
            if agent_id in active_discord_bots:
                del active_discord_bots[agent_id]
                
    task = asyncio.create_task(run_bot())
    active_discord_bots[agent_id] = {"client": client, "task": task}
    logging.info(f"[DISCORD] Spawned bot task for Agent {agent_id}")

async def stop_discord_bot(agent_id: int):
    """Stop the discord bot for a specific agent."""
    if agent_id in active_discord_bots:
        client = active_discord_bots[agent_id]["client"]
        await client.close()
        # task will finish when client closes
        del active_discord_bots[agent_id]
        logging.info(f"[DISCORD] Stopped bot for Agent {agent_id}")

async def fetch_timeline_context(agent_id: int, channel_id: int, limit: int = 10) -> str:
    """Fetch recent messages from the designated channel to build context."""
    if agent_id not in active_discord_bots:
        return ""
        
    client = active_discord_bots[agent_id]["client"]
    if not client.is_ready():
        return ""
        
    channel = client.get_channel(channel_id)
    if not channel:
        try:
            channel = await client.fetch_channel(channel_id)
        except:
            return ""
            
    if not isinstance(channel, discord.TextChannel):
        return ""
        
    history = []
    async for msg in channel.history(limit=limit):
        author_name = msg.author.display_name
        history.append(f"{author_name}: {msg.content}")
        
    if not history:
        return "The timeline is currently quiet."
        
    # Reverse to chronological order
    history.reverse()
    return "\n".join(history)

async def send_channel_message(agent_id: int, channel_id: int, text: str):
    """Send a message to a channel autonomously."""
    if agent_id not in active_discord_bots:
        return
        
    client = active_discord_bots[agent_id]["client"]
    if not client.is_ready():
        return
        
    channel = client.get_channel(channel_id)
    if not channel:
        try:
            channel = await client.fetch_channel(channel_id)
        except:
            return
            
    await channel.send(text)
